from django.conf import settings
from django.views import View

class Messages(View):
  """
  A class to manage messages with level, message, and count.
  """

  def __init__(self, user_is_staff=False):
    self.messages = []
    self.user_is_staff = user_is_staff

  def add(self, message, level='info'):
    """
    Add a message. If a message with the same level and message exists,
    increment the count by 1.

    Args:
        level (str): The level of the message (e.g., 'info', 'error').
        message (str): The message content.
    """
    for entry in self.messages:
      if entry['level'] == level and entry['message'] == message:
        entry['count'] += 1
        return
    # If no matching entry is found, add a new one
    self.messages.append({'level': level, 'message': str(message), 'count': 1})

  def get(self):
    """
    Retrieve all messages, excluding messages with level='debug' unless debug is True.

    Args:
        debug (bool): If True, include messages with level='debug'.

    Returns:
        list of dict: The filtered list of messages.
    """
    if getattr(settings, 'DEBUG', False) and self.user_is_staff:
      return self.messages
    return self.exclude(level='debug')

  def exclude(self, level=None, message=None):
    """
    Exclude messages based on level or message.

    Args:
        level (str, optional): The level to exclude (e.g., 'debug').
        message (str, optional): The message content to exclude.

    Returns:
        list of dict: The filtered list of messages.
    """
    filtered_messages = self.messages
    if level:
      filtered_messages = [msg for msg in filtered_messages if msg['level'] != level]
    if message:
      filtered_messages = [msg for msg in filtered_messages if msg['message'] != message]
    return filtered_messages
  
  def __str__(self):
    return self.get()
