"""
File: ragtag/tools/social.py
Project: Aura Friday MCP-Link Server
Component: Social Messaging Tool (Telegram Bot API)
Author: Christopher Nathan Drake (cnd)

Tool implementation for AI-to-human communication via Telegram Bot API.
Enables an AI agent to send messages, receive messages, manage chats,
and have interactive conversations with humans through a Telegram bot.

Uses only Python standard library (urllib) for HTTP calls - no external dependencies.

Copyright: (c) 2025 Christopher Nathan Drake. All rights reserved.
SPDX-License-Identifier: Proprietary
"signature": "СOОϹȠⲦᗞꓰ4𝟚𝟩ƊΤеƦе1i𝖠ΝıКVMКꓝꓐɡʋΟᏂꓮоⲘ𝕌þѡƼĸȷLЗΒυᒿꓖⲞցjDĵЗ𝟥ꓓ𐓒ꓰ×ꓔѵɋƍΕ7ᒿᏎՕŪꓳlⲘ𝟥ՕtUΜȣ𝟤ȜƎ𐓒ᴅꓖɅᴅ𐐕ĐΤ𝟫AOμoƊɋⴹⲦɋ9ΒP𝟢ƟjHÐх𝟑Ꮾꓠ"
"signdate": "2026-02-12T02:34:34.511Z",
"""

import json
import os
import threading
import time
import urllib.request
import urllib.parse
import urllib.error
import ssl
import hashlib
from collections import deque
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from easy_mcp.server import MCPLogger, get_tool_token
from ragtag.shared_config import get_config_manager, SharedConfigManager

# ============================================================================
# CONSTANTS
# ============================================================================

TOOL_LOG_NAME = "SOCIAL"
VERSION = "1.0.0"

# Module-level token generated once at import time
TOOL_UNLOCK_TOKEN = get_tool_token(__file__)

# Tool name with optional suffix from environment variable
TOOL_NAME_SUFFIX = os.environ.get("TOOL_SUFFIX", "")
TOOL_NAME = f"social{TOOL_NAME_SUFFIX}"

TELEGRAM_BOT_API_BASE_URL = "https://api.telegram.org/bot"

# How many recent messages to keep in memory per bot
MAX_TELEGRAM_MESSAGE_HISTORY_PER_BOT = 500

# ============================================================================
# GLOBAL STATE - Persistent across tool calls within a server session
# ============================================================================

# Lock for thread-safe access to all global telegram state
_telegram_global_state_lock = threading.Lock()

# Tracks the getUpdates offset per bot so we only fetch new messages
# Key: bot_token_short_hash -> Value: integer offset for next getUpdates call
_telegram_update_offset_per_bot = {}

# Tracks all chats that have interacted with each bot
# Key: bot_token_short_hash -> Value: {chat_id: chat_info_dict}
_telegram_known_chats_per_bot = {}

# Stores recent messages received per bot for the AI to review
# Key: bot_token_short_hash -> Value: deque of message dicts
_telegram_received_message_history_per_bot = {}

# Background polling threads per bot
# Key: bot_token_short_hash -> Value: {"thread": Thread, "running": bool, "token": str}
_telegram_background_pollers_per_bot = {}

# ============================================================================
# INTERNAL HELPER FUNCTIONS
# ============================================================================

def _create_short_hash_of_bot_token(bot_token: str) -> str:
  """Create a short SHA-256 hash of the bot token for use as dictionary key.
  Avoids storing raw tokens as dictionary keys in memory."""
  return hashlib.sha256(bot_token.encode()).hexdigest()[:16]


def _retrieve_telegram_bot_token_from_shared_config() -> Optional[str]:
  """Read the Telegram bot token from the shared nativemessaging.json config.
  Looks in settings[0].api_keys.TELEGRAM_BOT_TOKEN."""
  try:
    config_manager = get_config_manager()
    config = config_manager.load_config()
    telegram_bot_api_keys_section = SharedConfigManager.get_settings_value(config, 'api_keys', {})
    if isinstance(telegram_bot_api_keys_section, dict):
      return telegram_bot_api_keys_section.get('TELEGRAM_BOT_TOKEN')
    return None
  except Exception as e:
    MCPLogger.log(TOOL_LOG_NAME, f"Error reading bot token from config: {e}")
    return None


def _store_telegram_bot_token_into_shared_config(bot_token: str) -> bool:
  """Store a Telegram bot token into the shared nativemessaging.json config
  at settings[0].api_keys.TELEGRAM_BOT_TOKEN."""
  try:
    config_manager = get_config_manager()
    config = config_manager.load_config()
    telegram_bot_api_keys_section = SharedConfigManager.ensure_settings_section(config, 'api_keys')
    telegram_bot_api_keys_section['TELEGRAM_BOT_TOKEN'] = bot_token
    return config_manager.save_config(config)
  except Exception as e:
    MCPLogger.log(TOOL_LOG_NAME, f"Error storing bot token in config: {e}")
    return False


def _resolve_telegram_bot_token_from_params_or_config(params: Dict) -> Tuple[Optional[str], Optional[str]]:
  """Resolve the bot token: first from params, then from config.
  Returns (token, error_message). error_message is None on success."""
  token = params.get("bot_token")
  if token and isinstance(token, str) and token.strip():
    return token.strip(), None

  token = _retrieve_telegram_bot_token_from_shared_config()
  if token and isinstance(token, str) and token.strip():
    return token.strip(), None

  return None, ("No bot_token provided and none found in config. "
                "Either pass bot_token as a parameter, or use the set_bot_token operation first.")


def _call_telegram_bot_api_method(bot_token: str, api_method_name: str,
                                  request_parameters: Optional[Dict] = None,
                                  http_timeout_seconds: int = 30,
                                  max_retry_attempts: int = 3) -> Tuple[bool, Any]:
  """Execute a Telegram Bot API method via HTTPS POST (or GET if no params).

  Includes automatic retry with exponential backoff for transient network errors.
  Uses Connection: close header to prevent stale keep-alive connection reuse
  (which causes WinError 10054 on Windows after long-poll connections close).

  Args:
    bot_token: The bot's API token
    api_method_name: Telegram API method name (e.g. 'sendMessage', 'getUpdates')
    request_parameters: Optional dict of parameters for the API call
    http_timeout_seconds: HTTP request timeout
    max_retry_attempts: Maximum number of retry attempts for transient errors (default 3)

  Returns:
    Tuple of (success_bool, result_data_or_error_string)
  """
  url = f"{TELEGRAM_BOT_API_BASE_URL}{bot_token}/{api_method_name}"

  # These error signatures indicate transient network issues worth retrying.
  # WinError 10054 = WSAECONNRESET (connection reset by peer) - common on Windows
  #   when a prior long-poll HTTP keep-alive connection was closed server-side
  #   and urllib's default opener tries to reuse the dead socket.
  # WinError 10053 = WSAECONNABORTED (software caused connection abort)
  # "RemoteDisconnected" = http.client.RemoteDisconnected (server closed connection)
  # "ConnectionReset" = ConnectionResetError on Linux/macOS
  transient_network_error_signatures = [
    'WinError 10054',       # WSAECONNRESET - connection reset by peer
    'WinError 10053',       # WSAECONNABORTED - connection abort
    'RemoteDisconnected',   # http.client.RemoteDisconnected
    'ConnectionReset',      # ConnectionResetError (Linux/macOS equivalent)
    'BrokenPipeError',      # Broken pipe on Unix
    'ConnectionAborted',    # ConnectionAbortedError
    'EOF occurred',         # SSL EOF during read
    'timed out',            # Socket timeout (not the HTTP timeout - this is TCP level)
  ]

  last_error_message = ""

  for current_attempt_number in range(max_retry_attempts):
    try:
      if request_parameters:
        encoded_request_body = json.dumps(request_parameters).encode('utf-8')
        http_request = urllib.request.Request(
          url,
          data=encoded_request_body,
          headers={
            'Content-Type': 'application/json',
            # Force Connection: close to prevent HTTP keep-alive reuse.
            # This is the primary fix for WinError 10054: after a long-poll
            # getUpdates holds a connection open for 30+ seconds, the server
            # may close it. Without this header, urllib's default opener can
            # try to reuse the dead socket on the next request.
            'Connection': 'close',
          }
        )
      else:
        http_request = urllib.request.Request(url, headers={'Connection': 'close'})

      # Create a fresh SSL context for each attempt
      tls_ssl_context = ssl.create_default_context()

      with urllib.request.urlopen(http_request, timeout=http_timeout_seconds, context=tls_ssl_context) as http_response:
        response_body = json.loads(http_response.read().decode('utf-8'))

        if response_body.get('ok'):
          # Log if this succeeded on a retry (so we know retries are working)
          if current_attempt_number > 0:
            MCPLogger.log(TOOL_LOG_NAME, f"API call {api_method_name} succeeded on retry attempt {current_attempt_number + 1}")
          return True, response_body.get('result')
        else:
          # API-level errors (e.g. bad chat_id, message too long) are NOT transient - don't retry
          return False, response_body.get('description', 'Unknown Telegram API error')

    except urllib.error.HTTPError as http_error:
      # HTTP errors (4xx, 5xx) - only retry on 5xx (server errors)
      http_status_code = http_error.code
      try:
        error_response_body = json.loads(http_error.read().decode('utf-8'))
        last_error_message = error_response_body.get('description', f'HTTP {http_status_code}: {http_error.reason}')
      except Exception:
        last_error_message = f'HTTP {http_status_code}: {http_error.reason}'

      if http_status_code >= 500 and current_attempt_number < max_retry_attempts - 1:
        # Server error - worth retrying
        retry_delay_seconds = 0.5 * (2 ** current_attempt_number)  # 0.5s, 1s, 2s
        MCPLogger.log(TOOL_LOG_NAME, f"HTTP {http_status_code} from Telegram API on {api_method_name}, "
                       f"retrying in {retry_delay_seconds}s (attempt {current_attempt_number + 1}/{max_retry_attempts})")
        time.sleep(retry_delay_seconds)
        continue
      else:
        # Client error (4xx) or final attempt - return the error
        return False, last_error_message

    except (urllib.error.URLError, OSError, ConnectionError) as network_error:
      # Network-level errors - check if transient and worth retrying
      error_string = str(network_error)
      error_is_transient = any(signature in error_string for signature in transient_network_error_signatures)

      if error_is_transient and current_attempt_number < max_retry_attempts - 1:
        retry_delay_seconds = 0.5 * (2 ** current_attempt_number)  # 0.5s, 1s, 2s
        MCPLogger.log(TOOL_LOG_NAME, f"Transient network error on {api_method_name}: {error_string}. "
                       f"Retrying in {retry_delay_seconds}s (attempt {current_attempt_number + 1}/{max_retry_attempts})")
        time.sleep(retry_delay_seconds)
        last_error_message = f'Network error contacting Telegram API: {error_string}'
        continue
      else:
        # Non-transient error or final attempt
        return False, f'Network error contacting Telegram API: {error_string}'

    except Exception as general_error:
      # Unexpected errors - check if they look transient
      error_string = str(general_error)
      error_is_transient = any(signature in error_string for signature in transient_network_error_signatures)

      if error_is_transient and current_attempt_number < max_retry_attempts - 1:
        retry_delay_seconds = 0.5 * (2 ** current_attempt_number)
        MCPLogger.log(TOOL_LOG_NAME, f"Transient error on {api_method_name}: {error_string}. "
                       f"Retrying in {retry_delay_seconds}s (attempt {current_attempt_number + 1}/{max_retry_attempts})")
        time.sleep(retry_delay_seconds)
        last_error_message = f'Error calling Telegram API method {api_method_name}: {error_string}'
        continue
      else:
        return False, f'Error calling Telegram API method {api_method_name}: {error_string}'

  # All retries exhausted
  return False, f'All {max_retry_attempts} attempts failed for {api_method_name}. Last error: {last_error_message}'


def _record_chat_info_from_telegram_message(bot_token: str, message: Dict):
  """Extract and store chat information from a received Telegram message
  into the known-chats registry for this bot."""
  chat = message.get('chat', {})
  chat_id = chat.get('id')
  if not chat_id:
    return

  token_hash = _create_short_hash_of_bot_token(bot_token)

  with _telegram_global_state_lock:
    if token_hash not in _telegram_known_chats_per_bot:
      _telegram_known_chats_per_bot[token_hash] = {}
    _telegram_known_chats_per_bot[token_hash][chat_id] = {
      'id': chat_id,
      'type': chat.get('type', 'unknown'),
      'title': chat.get('title'),
      'first_name': chat.get('first_name'),
      'last_name': chat.get('last_name'),
      'username': chat.get('username'),
      'last_message_date': message.get('date'),
      'last_message_text': message.get('text', ''),
    }


def _append_message_to_telegram_history(bot_token: str, message: Dict):
  """Store a received message in the in-memory history deque for this bot."""
  token_hash = _create_short_hash_of_bot_token(bot_token)

  with _telegram_global_state_lock:
    if token_hash not in _telegram_received_message_history_per_bot:
      _telegram_received_message_history_per_bot[token_hash] = deque(
        maxlen=MAX_TELEGRAM_MESSAGE_HISTORY_PER_BOT
      )
    _telegram_received_message_history_per_bot[token_hash].append(message)


def _format_telegram_message_for_ai_display(message: Dict) -> Dict:
  """Format a raw Telegram message into a clean dict for AI consumption."""
  chat = message.get('chat', {})
  from_user = message.get('from', {})

  formatted = {
    'message_id': message.get('message_id'),
    'date': message.get('date'),
    'date_human_readable': datetime.fromtimestamp(
      message.get('date', 0), tz=timezone.utc
    ).strftime('%Y-%m-%d %H:%M:%S UTC') if message.get('date') else None,
    'chat_id': chat.get('id'),
    'chat_type': chat.get('type'),
    'chat_title_or_name': chat.get('title') or f"{chat.get('first_name', '')} {chat.get('last_name', '')}".strip(),
    'from_user_id': from_user.get('id'),
    'from_username': from_user.get('username'),
    'from_display_name': f"{from_user.get('first_name', '')} {from_user.get('last_name', '')}".strip(),
    'from_is_bot': from_user.get('is_bot', False),
    'text': message.get('text'),
  }

  # Include reply info if present
  reply_to = message.get('reply_to_message')
  if reply_to:
    formatted['reply_to_message_id'] = reply_to.get('message_id')
    formatted['reply_to_text_preview'] = (reply_to.get('text', '') or '')[:100]

  # Include photo info if present
  if message.get('photo'):
    formatted['has_photo'] = True
    formatted['photo_caption'] = message.get('caption')

  # Include document info if present
  if message.get('document'):
    doc = message['document']
    formatted['has_document'] = True
    formatted['document_file_name'] = doc.get('file_name')
    formatted['document_mime_type'] = doc.get('mime_type')

  # Include sticker info
  if message.get('sticker'):
    formatted['has_sticker'] = True
    formatted['sticker_emoji'] = message['sticker'].get('emoji')

  return formatted


def _process_telegram_updates_and_extract_messages(bot_token: str, updates: List[Dict]) -> List[Dict]:
  """Process a list of Telegram Update objects: track chats, store history,
  update offset, and return formatted messages for AI display."""
  token_hash = _create_short_hash_of_bot_token(bot_token)
  formatted_messages_for_ai = []

  for single_update in updates:
    update_id = single_update.get('update_id', 0)

    # Update the offset to be one past the highest update_id we've seen
    with _telegram_global_state_lock:
      current_offset = _telegram_update_offset_per_bot.get(token_hash, 0)
      if update_id >= current_offset:
        _telegram_update_offset_per_bot[token_hash] = update_id + 1

    # Extract the message (could be in 'message', 'edited_message', 'channel_post', etc.)
    message = (single_update.get('message')
               or single_update.get('edited_message')
               or single_update.get('channel_post')
               or single_update.get('edited_channel_post'))

    if message:
      _record_chat_info_from_telegram_message(bot_token, message)
      _append_message_to_telegram_history(bot_token, message)

      formatted = _format_telegram_message_for_ai_display(message)
      # Tag edited messages
      if single_update.get('edited_message') or single_update.get('edited_channel_post'):
        formatted['was_edited'] = True
      formatted_messages_for_ai.append(formatted)

    # Handle callback queries (inline button presses)
    callback_query = single_update.get('callback_query')
    if callback_query:
      formatted_messages_for_ai.append({
        'type': 'callback_query',
        'callback_query_id': callback_query.get('id'),
        'from_user_id': callback_query.get('from', {}).get('id'),
        'from_username': callback_query.get('from', {}).get('username'),
        'data': callback_query.get('data'),
        'message_id': callback_query.get('message', {}).get('message_id'),
        'chat_id': callback_query.get('message', {}).get('chat', {}).get('id'),
      })

  return formatted_messages_for_ai


# ============================================================================
# BACKGROUND POLLING (persistent listener)
# ============================================================================

def _telegram_background_polling_thread_function(bot_token: str, long_poll_timeout_seconds: int = 30):
  """Background thread that continuously polls Telegram for new messages.
  Messages are stored in the history deque for later retrieval by the AI."""
  token_hash = _create_short_hash_of_bot_token(bot_token)
  MCPLogger.log(TOOL_LOG_NAME, f"Background poller started for bot hash {token_hash[:8]}...")

  consecutive_error_count = 0
  max_backoff_seconds = 60

  while True:
    # Check if we should stop
    with _telegram_global_state_lock:
      poller_info = _telegram_background_pollers_per_bot.get(token_hash)
      if not poller_info or not poller_info.get('running'):
        MCPLogger.log(TOOL_LOG_NAME, f"Background poller stopping for bot hash {token_hash[:8]}")
        break

    # Build getUpdates parameters
    params = {
      'timeout': long_poll_timeout_seconds,
      'allowed_updates': ['message', 'edited_message', 'channel_post', 'callback_query']
    }

    with _telegram_global_state_lock:
      current_offset = _telegram_update_offset_per_bot.get(token_hash)
      if current_offset:
        params['offset'] = current_offset

    # Call getUpdates with long polling
    api_call_succeeded, api_result = _call_telegram_bot_api_method(
      bot_token, 'getUpdates', params,
      http_timeout_seconds=long_poll_timeout_seconds + 10  # HTTP timeout > long poll timeout
    )

    if api_call_succeeded:
      consecutive_error_count = 0
      if api_result:  # Non-empty list of updates
        _process_telegram_updates_and_extract_messages(bot_token, api_result)
        MCPLogger.log(TOOL_LOG_NAME, f"Background poller received {len(api_result)} update(s)")
    else:
      consecutive_error_count += 1
      backoff_delay = min(2 ** consecutive_error_count, max_backoff_seconds)
      MCPLogger.log(TOOL_LOG_NAME, f"Background poller error (attempt {consecutive_error_count}): {api_result}. Backing off {backoff_delay}s")
      time.sleep(backoff_delay)

  MCPLogger.log(TOOL_LOG_NAME, f"Background poller exited for bot hash {token_hash[:8]}")


# ============================================================================
# OPERATION HANDLERS
# ============================================================================

def handle_set_bot_token_operation(params: Dict) -> Dict:
  """Handle set_bot_token operation - stores token in config and validates it."""
  bot_token = params.get("bot_token")
  if not bot_token or not isinstance(bot_token, str) or not bot_token.strip():
    return create_error_response("Parameter 'bot_token' is required. Provide a Telegram Bot API token (from @BotFather).", with_readme=True)

  bot_token = bot_token.strip()

  # Validate token by calling getMe
  MCPLogger.log(TOOL_LOG_NAME, "Validating bot token via getMe...")
  api_call_succeeded, api_result = _call_telegram_bot_api_method(bot_token, 'getMe')

  if not api_call_succeeded:
    return create_error_response(f"Invalid bot token - Telegram API rejected it: {api_result}", with_readme=False)

  # Store in config
  token_stored_successfully = _store_telegram_bot_token_into_shared_config(bot_token)

  bot_username = api_result.get('username', 'unknown')
  bot_display_name = f"{api_result.get('first_name', '')} {api_result.get('last_name', '')}".strip()

  storage_status = "saved to config" if token_stored_successfully else "NOT saved to config (error)"

  return {
    "content": [{
      "type": "text",
      "text": json.dumps({
        "status": "success",
        "bot_username": f"@{bot_username}",
        "bot_display_name": bot_display_name,
        "bot_id": api_result.get('id'),
        "token_storage_status": storage_status,
        "can_join_groups": api_result.get('can_join_groups', False),
        "can_read_all_group_messages": api_result.get('can_read_all_group_messages', False),
      }, indent=2)
    }],
    "isError": False
  }


def handle_get_bot_info_operation(params: Dict) -> Dict:
  """Handle get_bot_info operation - returns bot identity via getMe."""
  bot_token, token_error = _resolve_telegram_bot_token_from_params_or_config(params)
  if token_error:
    return create_error_response(token_error, with_readme=True)

  api_call_succeeded, api_result = _call_telegram_bot_api_method(bot_token, 'getMe')
  if not api_call_succeeded:
    return create_error_response(f"getMe failed: {api_result}", with_readme=False)

  return {
    "content": [{
      "type": "text",
      "text": json.dumps({
        "bot_id": api_result.get('id'),
        "bot_username": f"@{api_result.get('username', 'unknown')}",
        "bot_display_name": f"{api_result.get('first_name', '')} {api_result.get('last_name', '')}".strip(),
        "is_bot": api_result.get('is_bot'),
        "can_join_groups": api_result.get('can_join_groups'),
        "can_read_all_group_messages": api_result.get('can_read_all_group_messages'),
        "supports_inline_queries": api_result.get('supports_inline_queries'),
      }, indent=2)
    }],
    "isError": False
  }


def handle_send_message_operation(params: Dict) -> Dict:
  """Handle send_message operation - sends a text message to a Telegram chat."""
  bot_token, token_error = _resolve_telegram_bot_token_from_params_or_config(params)
  if token_error:
    return create_error_response(token_error, with_readme=True)

  chat_id = params.get("chat_id")
  text = params.get("text")

  if not chat_id:
    return create_error_response("Parameter 'chat_id' is required. Use get_updates or list_known_chats to find chat IDs.", with_readme=False)
  if not text:
    return create_error_response("Parameter 'text' is required. Provide the message text to send.", with_readme=False)

  api_params = {
    'chat_id': chat_id,
    'text': text,
  }

  # Optional: parse mode (HTML or Markdown)
  parse_mode = params.get("parse_mode")
  if parse_mode:
    api_params['parse_mode'] = parse_mode

  # Optional: reply to a specific message
  reply_to_message_id = params.get("reply_to_message_id")
  if reply_to_message_id:
    api_params['reply_parameters'] = {'message_id': reply_to_message_id}

  # Optional: disable link preview
  if params.get("disable_link_preview"):
    api_params['link_preview_options'] = {'is_disabled': True}

  MCPLogger.log(TOOL_LOG_NAME, f"Sending message to chat_id={chat_id}, text length={len(text)}")

  api_call_succeeded, api_result = _call_telegram_bot_api_method(bot_token, 'sendMessage', api_params)
  if not api_call_succeeded:
    return create_error_response(f"sendMessage failed: {api_result}", with_readme=False)

  sent_message_id = api_result.get('message_id')
  MCPLogger.log(TOOL_LOG_NAME, f"Message sent successfully, message_id={sent_message_id}")

  return {
    "content": [{
      "type": "text",
      "text": json.dumps({
        "status": "sent",
        "message_id": sent_message_id,
        "chat_id": chat_id,
        "date": api_result.get('date'),
      }, indent=2)
    }],
    "isError": False
  }


def handle_get_updates_operation(params: Dict) -> Dict:
  """Handle get_updates operation - polls Telegram for new messages.
  Uses long-polling with configurable timeout. Tracks offset to only return new messages."""
  bot_token, token_error = _resolve_telegram_bot_token_from_params_or_config(params)
  if token_error:
    return create_error_response(token_error, with_readme=True)

  token_hash = _create_short_hash_of_bot_token(bot_token)
  long_poll_timeout = params.get("timeout", 5)  # Default 5 seconds

  # Clamp timeout to reasonable range
  long_poll_timeout = max(0, min(long_poll_timeout, 30))

  api_params = {
    'timeout': long_poll_timeout,
    'allowed_updates': ['message', 'edited_message', 'channel_post', 'callback_query']
  }

  # Use stored offset to only get new updates
  with _telegram_global_state_lock:
    current_offset = _telegram_update_offset_per_bot.get(token_hash)
    if current_offset:
      api_params['offset'] = current_offset

  MCPLogger.log(TOOL_LOG_NAME, f"Polling for updates (timeout={long_poll_timeout}s, offset={api_params.get('offset', 'none')})")

  api_call_succeeded, api_result = _call_telegram_bot_api_method(
    bot_token, 'getUpdates', api_params,
    http_timeout_seconds=long_poll_timeout + 10
  )

  if not api_call_succeeded:
    return create_error_response(f"getUpdates failed: {api_result}", with_readme=False)

  # Process updates and format messages
  formatted_messages = _process_telegram_updates_and_extract_messages(bot_token, api_result or [])

  return {
    "content": [{
      "type": "text",
      "text": json.dumps({
        "update_count": len(api_result or []),
        "messages": formatted_messages,
        "note": "Call get_updates again to check for newer messages" if formatted_messages else "No new messages. Call get_updates again later or increase timeout for long-polling."
      }, indent=2)
    }],
    "isError": False
  }


def handle_list_known_chats_operation(params: Dict) -> Dict:
  """Handle list_known_chats - returns all chats that have interacted with the bot."""
  bot_token, token_error = _resolve_telegram_bot_token_from_params_or_config(params)
  if token_error:
    return create_error_response(token_error, with_readme=True)

  token_hash = _create_short_hash_of_bot_token(bot_token)

  with _telegram_global_state_lock:
    known_chats = _telegram_known_chats_per_bot.get(token_hash, {})
    chats_list = list(known_chats.values())

  if not chats_list:
    return {
      "content": [{
        "type": "text",
        "text": json.dumps({
          "chats": [],
          "note": "No chats known yet. The bot needs to receive at least one message first. Ask someone to message the bot, or use get_updates to poll for messages."
        }, indent=2)
      }],
      "isError": False
    }

  return {
    "content": [{
      "type": "text",
      "text": json.dumps({
        "chat_count": len(chats_list),
        "chats": chats_list
      }, indent=2)
    }],
    "isError": False
  }


def handle_get_message_history_operation(params: Dict) -> Dict:
  """Handle get_message_history - returns stored messages from the in-memory history."""
  bot_token, token_error = _resolve_telegram_bot_token_from_params_or_config(params)
  if token_error:
    return create_error_response(token_error, with_readme=True)

  token_hash = _create_short_hash_of_bot_token(bot_token)
  max_messages_to_return = params.get("limit", 20)
  filter_chat_id = params.get("chat_id")

  with _telegram_global_state_lock:
    history_deque = _telegram_received_message_history_per_bot.get(token_hash, deque())
    all_messages = list(history_deque)

  # Format messages for AI
  formatted = [_format_telegram_message_for_ai_display(msg) for msg in all_messages]

  # Apply chat_id filter if specified
  if filter_chat_id:
    formatted = [m for m in formatted if m.get('chat_id') == filter_chat_id]

  # Return only the most recent N messages
  recent_messages = formatted[-max_messages_to_return:]

  return {
    "content": [{
      "type": "text",
      "text": json.dumps({
        "total_stored_message_count": len(all_messages),
        "returned_message_count": len(recent_messages),
        "messages": recent_messages
      }, indent=2)
    }],
    "isError": False
  }


def handle_edit_message_operation(params: Dict) -> Dict:
  """Handle edit_message operation - edits a previously sent message."""
  bot_token, token_error = _resolve_telegram_bot_token_from_params_or_config(params)
  if token_error:
    return create_error_response(token_error, with_readme=True)

  chat_id = params.get("chat_id")
  message_id = params.get("message_id")
  text = params.get("text")

  if not chat_id:
    return create_error_response("Parameter 'chat_id' is required.", with_readme=False)
  if not message_id:
    return create_error_response("Parameter 'message_id' is required.", with_readme=False)
  if not text:
    return create_error_response("Parameter 'text' is required.", with_readme=False)

  api_params = {
    'chat_id': chat_id,
    'message_id': message_id,
    'text': text,
  }

  parse_mode = params.get("parse_mode")
  if parse_mode:
    api_params['parse_mode'] = parse_mode

  api_call_succeeded, api_result = _call_telegram_bot_api_method(bot_token, 'editMessageText', api_params)
  if not api_call_succeeded:
    return create_error_response(f"editMessageText failed: {api_result}", with_readme=False)

  return {
    "content": [{
      "type": "text",
      "text": json.dumps({"status": "edited", "message_id": message_id, "chat_id": chat_id}, indent=2)
    }],
    "isError": False
  }


def handle_delete_message_operation(params: Dict) -> Dict:
  """Handle delete_message operation - deletes a message."""
  bot_token, token_error = _resolve_telegram_bot_token_from_params_or_config(params)
  if token_error:
    return create_error_response(token_error, with_readme=True)

  chat_id = params.get("chat_id")
  message_id = params.get("message_id")

  if not chat_id:
    return create_error_response("Parameter 'chat_id' is required.", with_readme=False)
  if not message_id:
    return create_error_response("Parameter 'message_id' is required.", with_readme=False)

  api_params = {
    'chat_id': chat_id,
    'message_id': message_id,
  }

  api_call_succeeded, api_result = _call_telegram_bot_api_method(bot_token, 'deleteMessage', api_params)
  if not api_call_succeeded:
    return create_error_response(f"deleteMessage failed: {api_result}", with_readme=False)

  return {
    "content": [{
      "type": "text",
      "text": json.dumps({"status": "deleted", "message_id": message_id, "chat_id": chat_id}, indent=2)
    }],
    "isError": False
  }


def handle_send_photo_operation(params: Dict) -> Dict:
  """Handle send_photo operation - sends a photo to a chat via URL."""
  bot_token, token_error = _resolve_telegram_bot_token_from_params_or_config(params)
  if token_error:
    return create_error_response(token_error, with_readme=True)

  chat_id = params.get("chat_id")
  photo_url = params.get("photo_url")

  if not chat_id:
    return create_error_response("Parameter 'chat_id' is required.", with_readme=False)
  if not photo_url:
    return create_error_response("Parameter 'photo_url' is required. Provide a public URL to an image.", with_readme=False)

  api_params = {
    'chat_id': chat_id,
    'photo': photo_url,
  }

  caption = params.get("caption")
  if caption:
    api_params['caption'] = caption

  parse_mode = params.get("parse_mode")
  if parse_mode:
    api_params['parse_mode'] = parse_mode

  reply_to_message_id = params.get("reply_to_message_id")
  if reply_to_message_id:
    api_params['reply_parameters'] = {'message_id': reply_to_message_id}

  api_call_succeeded, api_result = _call_telegram_bot_api_method(bot_token, 'sendPhoto', api_params)
  if not api_call_succeeded:
    return create_error_response(f"sendPhoto failed: {api_result}", with_readme=False)

  return {
    "content": [{
      "type": "text",
      "text": json.dumps({
        "status": "sent",
        "message_id": api_result.get('message_id'),
        "chat_id": chat_id,
      }, indent=2)
    }],
    "isError": False
  }


def handle_start_listening_operation(params: Dict) -> Dict:
  """Handle start_listening operation - starts a background polling thread."""
  bot_token, token_error = _resolve_telegram_bot_token_from_params_or_config(params)
  if token_error:
    return create_error_response(token_error, with_readme=True)

  token_hash = _create_short_hash_of_bot_token(bot_token)

  with _telegram_global_state_lock:
    existing_poller = _telegram_background_pollers_per_bot.get(token_hash)
    if existing_poller and existing_poller.get('running'):
      return {
        "content": [{"type": "text", "text": json.dumps({
          "status": "already_running",
          "note": "Background listener is already running for this bot."
        }, indent=2)}],
        "isError": False
      }

  # Start the background polling thread
  poller_thread = threading.Thread(
    target=_telegram_background_polling_thread_function,
    args=(bot_token,),
    daemon=True,
    name=f"telegram_poller_{token_hash[:8]}"
  )

  with _telegram_global_state_lock:
    _telegram_background_pollers_per_bot[token_hash] = {
      'thread': poller_thread,
      'running': True,
      'token': bot_token,
      'started_at': datetime.now(timezone.utc).isoformat(),
    }

  poller_thread.start()
  MCPLogger.log(TOOL_LOG_NAME, f"Started background listener for bot hash {token_hash[:8]}")

  return {
    "content": [{"type": "text", "text": json.dumps({
      "status": "started",
      "note": "Background listener is now running. Messages will accumulate in history. Use get_message_history or get_updates to read them."
    }, indent=2)}],
    "isError": False
  }


def handle_stop_listening_operation(params: Dict) -> Dict:
  """Handle stop_listening operation - stops the background polling thread."""
  bot_token, token_error = _resolve_telegram_bot_token_from_params_or_config(params)
  if token_error:
    return create_error_response(token_error, with_readme=True)

  token_hash = _create_short_hash_of_bot_token(bot_token)

  with _telegram_global_state_lock:
    existing_poller = _telegram_background_pollers_per_bot.get(token_hash)
    if not existing_poller or not existing_poller.get('running'):
      return {
        "content": [{"type": "text", "text": json.dumps({
          "status": "not_running",
          "note": "No background listener is running for this bot."
        }, indent=2)}],
        "isError": False
      }

    existing_poller['running'] = False

  MCPLogger.log(TOOL_LOG_NAME, f"Stopping background listener for bot hash {token_hash[:8]}")

  return {
    "content": [{"type": "text", "text": json.dumps({
      "status": "stopping",
      "note": "Background listener is being stopped. It will terminate after the current poll completes (up to 30 seconds)."
    }, indent=2)}],
    "isError": False
  }


def handle_get_listening_status_operation(params: Dict) -> Dict:
  """Handle get_listening_status - returns whether background polling is active."""
  bot_token, token_error = _resolve_telegram_bot_token_from_params_or_config(params)
  if token_error:
    return create_error_response(token_error, with_readme=True)

  token_hash = _create_short_hash_of_bot_token(bot_token)

  with _telegram_global_state_lock:
    existing_poller = _telegram_background_pollers_per_bot.get(token_hash)
    history_count = len(_telegram_received_message_history_per_bot.get(token_hash, []))
    known_chat_count = len(_telegram_known_chats_per_bot.get(token_hash, {}))

  if existing_poller and existing_poller.get('running'):
    is_thread_actually_alive = existing_poller['thread'].is_alive()
    return {
      "content": [{"type": "text", "text": json.dumps({
        "listening": True,
        "thread_alive": is_thread_actually_alive,
        "started_at": existing_poller.get('started_at'),
        "stored_message_count": history_count,
        "known_chat_count": known_chat_count,
      }, indent=2)}],
      "isError": False
    }
  else:
    return {
      "content": [{"type": "text", "text": json.dumps({
        "listening": False,
        "stored_message_count": history_count,
        "known_chat_count": known_chat_count,
      }, indent=2)}],
      "isError": False
    }


# ============================================================================
# MCP TOOL DEFINITION
# ============================================================================

TOOLS = [
  {
    "name": TOOL_NAME,
    "description": """Send and receive messages via Telegram bot. Enables AI-to-human chat, group messaging, and interactive conversations.
- Use this tool when you need to communicate with humans via Telegram
""",
    "parameters": {
      "properties": {
        "input": {
          "type": "object",
          "description": "All tool parameters are passed in this single dict. Use {\"input\":{\"operation\":\"readme\"}} to get full documentation, parameters, and an unlock token."
        }
      },
      "required": [],
      "type": "object"
    },
    "real_parameters": {
      "properties": {
        "operation": {
          "type": "string",
          "enum": [
            "readme", "set_bot_token", "get_bot_info",
            "send_message", "get_updates", "list_known_chats",
            "get_message_history", "edit_message", "delete_message",
            "send_photo", "start_listening", "stop_listening",
            "get_listening_status"
          ],
          "description": "Operation to perform"
        },
        "bot_token": {
          "type": "string",
          "description": "Telegram Bot API token (from @BotFather). Optional if previously stored via set_bot_token."
        },
        "chat_id": {
          "type": "integer",
          "description": "Telegram chat ID to send messages to. Get this from get_updates or list_known_chats."
        },
        "text": {
          "type": "string",
          "description": "Message text to send (for send_message, edit_message)"
        },
        "message_id": {
          "type": "integer",
          "description": "Message ID (for edit_message, delete_message, reply_to_message_id)"
        },
        "reply_to_message_id": {
          "type": "integer",
          "description": "Message ID to reply to (for send_message, send_photo)"
        },
        "parse_mode": {
          "type": "string",
          "enum": ["HTML", "Markdown", "MarkdownV2"],
          "description": "Text formatting mode (optional)"
        },
        "disable_link_preview": {
          "type": "boolean",
          "default": False,
          "description": "Disable link previews in messages"
        },
        "photo_url": {
          "type": "string",
          "description": "Public URL of photo to send (for send_photo)"
        },
        "caption": {
          "type": "string",
          "description": "Caption for photo (for send_photo)"
        },
        "timeout": {
          "type": "integer",
          "default": 5,
          "description": "Long-polling timeout in seconds for get_updates (0-30)"
        },
        "limit": {
          "type": "integer",
          "default": 20,
          "description": "Max messages to return (for get_message_history)"
        },
        "tool_unlock_token": {
          "type": "string",
          "description": "Security token, " + TOOL_UNLOCK_TOKEN + ", obtained from readme operation"
        }
      },
      "required": ["operation", "tool_unlock_token"],
      "type": "object"
    },
    "readme": """
# Social Tool - Telegram Bot API Integration

Enables AI-to-human communication via Telegram bots. Send messages, receive replies,
manage conversations, and interact with users in real-time.

## Usage-Safety Token

Your tool_unlock_token for this installation is: """ + TOOL_UNLOCK_TOKEN + """

You MUST include tool_unlock_token in the input dict for all operations (except readme).

## Quick Start

### 1. Set your bot token (one-time setup)
```json
{"input": {"operation": "set_bot_token", "bot_token": "YOUR_BOT_TOKEN_FROM_BOTFATHER", "tool_unlock_token": \"""" + TOOL_UNLOCK_TOKEN + """\"}}
```

### 2. Check bot identity
```json
{"input": {"operation": "get_bot_info", "tool_unlock_token": \"""" + TOOL_UNLOCK_TOKEN + """\"}}
```

### 3. Poll for incoming messages (someone must message the bot first!)
```json
{"input": {"operation": "get_updates", "timeout": 10, "tool_unlock_token": \"""" + TOOL_UNLOCK_TOKEN + """\"}}
```

### 4. Send a message to a chat
```json
{"input": {"operation": "send_message", "chat_id": 123456789, "text": "Hello from AI!", "tool_unlock_token": \"""" + TOOL_UNLOCK_TOKEN + """\"}}
```

### 5. Reply to a specific message
```json
{"input": {"operation": "send_message", "chat_id": 123456789, "text": "This is a reply!", "reply_to_message_id": 42, "tool_unlock_token": \"""" + TOOL_UNLOCK_TOKEN + """\"}}
```

## Operations

### set_bot_token
Store and validate a Telegram bot token. Get tokens from @BotFather on Telegram.
- Required: bot_token

### get_bot_info
Get information about the configured bot (username, ID, capabilities).

### send_message
Send a text message to a chat.
- Required: chat_id, text
- Optional: parse_mode (HTML/Markdown/MarkdownV2), reply_to_message_id, disable_link_preview

### get_updates
Poll Telegram for new incoming messages. Uses long-polling.
- Optional: timeout (0-30 seconds, default 5)
- Returns new messages since last poll. Call repeatedly to stay updated.
- The offset is tracked automatically so you only get NEW messages each time.

### list_known_chats
List all chats that have sent messages to the bot. Useful for finding chat_id values.

### get_message_history
Retrieve stored messages from in-memory history (last """ + str(MAX_TELEGRAM_MESSAGE_HISTORY_PER_BOT) + """ messages).
- Optional: limit (default 20), chat_id (filter to specific chat)

### edit_message
Edit a previously sent message.
- Required: chat_id, message_id, text
- Optional: parse_mode

### delete_message
Delete a message (bot must have permission).
- Required: chat_id, message_id

### send_photo
Send a photo to a chat via URL.
- Required: chat_id, photo_url
- Optional: caption, parse_mode, reply_to_message_id

### start_listening
Start a background thread that continuously polls for messages.
Messages accumulate in history for later retrieval.

### stop_listening
Stop the background polling thread.

### get_listening_status
Check if background listening is active and view stats.

## Workflow Tips

1. **Finding chat_id**: Have the human send any message to the bot, then call get_updates to see the chat_id.
2. **Conversations**: Alternate between send_message and get_updates to have a back-and-forth conversation.
3. **Background mode**: Use start_listening for continuous monitoring, then get_message_history to read accumulated messages.
4. **Rich text**: Use parse_mode="HTML" with <b>bold</b>, <i>italic</i>, <code>code</code>, <a href="url">links</a>.

## Notes
- Bot tokens can be passed per-call via bot_token parameter, or stored once via set_bot_token.
- The bot can only receive messages from users who have started a conversation with it (/start).
- Group messages require the bot to be added to the group.
- Message history is stored in-memory and cleared when the server restarts.
"""
  }
]


# ============================================================================
# PARAMETER VALIDATION
# ============================================================================

def validate_parameters(input_param: Dict) -> Tuple[Optional[str], Dict]:
  """Validate input parameters against the real_parameters schema.

  Returns:
    Tuple of (error_message_or_none, validated_params_dict)
  """
  real_params_schema = TOOLS[0]["real_parameters"]
  properties = real_params_schema["properties"]
  required = real_params_schema.get("required", [])

  # For readme operation, don't require token
  operation = input_param.get("operation")
  if operation == "readme":
    required = ["operation"]

  # Check for unexpected parameters
  expected_params = set(properties.keys())
  provided_params = set(input_param.keys())
  unexpected_params = provided_params - expected_params

  if unexpected_params:
    return (f"Unexpected parameters: {', '.join(sorted(unexpected_params))}. "
            f"Expected: {', '.join(sorted(expected_params))}"), {}

  # Check for missing required parameters
  missing_required = set(required) - provided_params
  if missing_required:
    return f"Missing required parameters: {', '.join(sorted(missing_required))}", {}

  # Validate types and extract values
  validated = {}
  for param_name, param_schema in properties.items():
    if param_name in input_param:
      value = input_param[param_name]
      expected_type = param_schema.get("type")

      if expected_type == "string" and not isinstance(value, str):
        return f"Parameter '{param_name}' must be a string, got {type(value).__name__}", {}
      elif expected_type == "integer" and not isinstance(value, int):
        # Allow string chat_id (Telegram accepts both)
        if param_name == "chat_id" and isinstance(value, str):
          try:
            value = int(value)
          except ValueError:
            return f"Parameter '{param_name}' must be an integer, got non-numeric string", {}
        elif not isinstance(value, int):
          return f"Parameter '{param_name}' must be an integer, got {type(value).__name__}", {}
      elif expected_type == "boolean" and not isinstance(value, bool):
        return f"Parameter '{param_name}' must be a boolean, got {type(value).__name__}", {}

      # Enum validation
      if "enum" in param_schema:
        allowed_values = param_schema["enum"]
        if value not in allowed_values:
          return f"Parameter '{param_name}' must be one of {allowed_values}, got '{value}'", {}

      validated[param_name] = value
    elif param_name in required:
      return f"Required parameter '{param_name}' is missing", {}
    else:
      default_value = param_schema.get("default")
      if default_value is not None:
        validated[param_name] = default_value

  return None, validated


# ============================================================================
# README AND ERROR HELPERS
# ============================================================================

def readme(with_readme: bool = True) -> str:
  """Return tool documentation."""
  try:
    if not with_readme:
      return ''
    MCPLogger.log(TOOL_LOG_NAME, "Processing readme request")
    return "\n\n" + json.dumps({
      "description": TOOLS[0]["readme"],
      "parameters": TOOLS[0]["real_parameters"]
    }, indent=2)
  except Exception as e:
    MCPLogger.log(TOOL_LOG_NAME, f"Error processing readme request: {str(e)}")
    return ''


def create_error_response(error_msg: str, with_readme: bool = True) -> Dict:
  """Log and create an error response, optionally including the tool documentation."""
  MCPLogger.log(TOOL_LOG_NAME, f"Error: {error_msg}")
  return {
    "content": [{"type": "text", "text": f"{error_msg}{readme(with_readme)}"}],
    "isError": True
  }


# ============================================================================
# MAIN TOOL HANDLER
# ============================================================================

def handle_social(input_param: Dict) -> Dict:
  """Main entry point for the social tool - routes operations to handlers."""
  try:
    # Pop off synthetic handler_info parameter early (before validation)
    handler_info = input_param.pop('handler_info', None)

    # Collapse the single-input wrapper
    if isinstance(input_param, dict) and "input" in input_param:
      input_param = input_param["input"]

    # Handle readme operation first (before token validation)
    if isinstance(input_param, dict) and input_param.get("operation") == "readme":
      return {
        "content": [{"type": "text", "text": readme(True)}],
        "isError": False
      }

    # Validate input structure
    if not isinstance(input_param, dict):
      return create_error_response("Invalid input format. Expected dictionary with tool parameters.", with_readme=True)

    # Check for token - if missing or invalid, return readme
    provided_token = input_param.get("tool_unlock_token")
    if provided_token != TOOL_UNLOCK_TOKEN:
      return create_error_response(
        "Invalid or missing tool_unlock_token. Read the documentation below to get the correct token:",
        with_readme=True
      )

    # Validate all parameters using schema
    error_msg, validated_params = validate_parameters(input_param)
    if error_msg:
      return create_error_response(error_msg, with_readme=True)

    # Extract operation and route
    operation = validated_params.get("operation")

    if operation == "set_bot_token":
      return handle_set_bot_token_operation(validated_params)
    elif operation == "get_bot_info":
      return handle_get_bot_info_operation(validated_params)
    elif operation == "send_message":
      return handle_send_message_operation(validated_params)
    elif operation == "get_updates":
      return handle_get_updates_operation(validated_params)
    elif operation == "list_known_chats":
      return handle_list_known_chats_operation(validated_params)
    elif operation == "get_message_history":
      return handle_get_message_history_operation(validated_params)
    elif operation == "edit_message":
      return handle_edit_message_operation(validated_params)
    elif operation == "delete_message":
      return handle_delete_message_operation(validated_params)
    elif operation == "send_photo":
      return handle_send_photo_operation(validated_params)
    elif operation == "start_listening":
      return handle_start_listening_operation(validated_params)
    elif operation == "stop_listening":
      return handle_stop_listening_operation(validated_params)
    elif operation == "get_listening_status":
      return handle_get_listening_status_operation(validated_params)
    elif operation == "readme":
      return {
        "content": [{"type": "text", "text": readme(True)}],
        "isError": False
      }
    else:
      valid_operations = TOOLS[0]["real_parameters"]["properties"]["operation"]["enum"]
      return create_error_response(
        f"Unknown operation: '{operation}'. Available: {', '.join(valid_operations)}",
        with_readme=True
      )

  except Exception as e:
    return create_error_response(f"Error in social operation: {str(e)}", with_readme=True)


# ============================================================================
# TOOL REGISTRATION
# ============================================================================

HANDLERS = {
  TOOL_NAME: handle_social
}
