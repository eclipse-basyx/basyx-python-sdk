# Copyright 2019 PyI40AAS Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
"""
Message Logger to store LoggingMessages
"""
from enum import Flag, auto
from typing import List, Tuple, Optional


class MessageCategory(Flag):
    ERROR = auto()
    WARNING = auto()
    SUCCESS = auto()
    ALL = ERROR | WARNING | SUCCESS


class LoggingMessage():
    """
    A LoggingMessage is a data structure for logging messages using the compliance tool
    """

    def __init__(self,
                 msg: str,
                 msg_category: str,
                 category: MessageCategory):
        """
        Initializer of Asset

        :param msg: Message for information in which function the msg_category occurred
        :param msg_category: Message which occurred (error message or warning or info)
        :param category: Kind of message occurred (Error, Warning, Info)
        """
        super().__init__()
        self.msg: str = msg
        self.msg_category: str = msg_category
        self.category: MessageCategory = category

    def __str__(self, deep=False):
        if self.msg_category and (self.category & MessageCategory.ERROR or self.category & MessageCategory.WARNING or
                                  deep):
            return '{}: {}\nOccurred log messages:\n{}\n'.format(self.category.name, self.msg, self.msg_category)
        else:
            return '{}: {}\n'.format(self.category.name, self.msg)


class MessageLogger():
    """
    A MessageLogger stores LoggingMessages and can do evaluation on them
    :ivar messages: List of LoggingMessages
    :ivar error: Flag: bool, if an error is in any of the LoggingMessages, otherwise false
    """
    def __init__(self):
        """
        Initializer of Asset
        """
        super().__init__()
        self.messages: List[LoggingMessage] = []
        self.error: bool = False

    def add_msg(self, msg: LoggingMessage):
        self.messages.append(msg)
        if msg.category == MessageCategory.ERROR:
            self.error = True

    def get_messages_in_list(self, flags: MessageCategory) -> List[LoggingMessage]:
        msg_list = []
        for x in self.messages:
            if x.category & flags:
                msg_list.append(x)
        return msg_list

    def get_last_message_in_list(self, flags: MessageCategory) -> Optional[LoggingMessage]:
        for x in reversed(self.messages):
            if x.category & flags:
                return x
        return None

    def get_messages_in_ordered_lists(self) -> Tuple[List[LoggingMessage], List[LoggingMessage], List[LoggingMessage]]:
        error_list = []
        warning_list = []
        info_list = []
        for x in self.messages:
            if x.msg_category == MessageCategory.ERROR:
                error_list.append(x)
            elif x.msg_category == MessageCategory.WARNING:
                warning_list.append(x)
            elif x.msg_category == MessageCategory.SUCCESS:
                info_list.append(x)
            else:
                raise ValueError()
        return error_list, warning_list, info_list
