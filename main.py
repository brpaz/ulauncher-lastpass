""" Main Module """

import logging
import re

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.item.ExtensionSmallResultItem import ExtensionSmallResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction
from lastpass.lastpass import Lastpass
from lastpass.errors import LastPassError

logger = logging.getLogger(__name__)


class LastpassExtension(Extension):
    """ Main Extension Class  """
    def __init__(self):
        """ Initializes the extension """
        super(LastpassExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())
        self.lp = Lastpass()

    def list_passwords(self, query):
        """ Lists passwords from LastPass vault """

        try:
            pwds = self.lp.get_passwords(query)

            return self.list_passwords_result(pwds)

        except LastPassError as e:
            return RenderResultListAction([
                ExtensionResultItem(icon='images/icon.png',
                                    name=e.output,
                                    description='LastPass Error',
                                    highlightable=False,
                                    on_enter=HideWindowAction())
            ])

    def list_passwords_result(self, pwds=[]):
        if not pwds:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='No passwords found matching your criteria',
                    highlightable=False,
                    on_enter=HideWindowAction())
            ])

        items = []
        for pwd in pwds[:8]:
            items.append(
                ExtensionResultItem(icon='images/icon.png',
                                    name=pwd["name"],
                                    description=pwd["folder"],
                                    on_enter=ExtensionCustomAction(
                                        {'id': pwd['id']},
                                        keep_app_open=True)))

        return RenderResultListAction(items)

    def show_lpass_not_installed_message(self):
        """ Displays a info message when the user doesn´t have the lpass cli installed """
        return RenderResultListAction([
            ExtensionResultItem(
                icon='images/icon.png',
                name='lpass cli was not found on your system.',
                description="Press enter and follow the instructions for your system",
                highlightable=False,
                on_enter=OpenUrlAction(
                    "https://github.com/lastpass/lastpass-cli"))
        ])

    def show_not_authenticated_message(self):
        """ Displays a message with instructions for unauthenticated users """
        return RenderResultListAction([
            ExtensionResultItem(
                icon='images/icon.png',
                name='you are not logged in on LastPass',
                description="Open a terminal and run lpass login <username> to login.",
                highlightable=False,
                on_enter=HideWindowAction())
        ])


class KeywordQueryEventListener(EventListener):
    """ Listener that handles the user input """

    # pylint: disable=unused-argument,no-self-use
    def on_event(self, event, extension):
        """ Handles the event """
        query = event.get_argument() or ""

        if not extension.lp.is_cli_installed():
            return extension.show_lpass_not_installed_message()

        if not extension.lp.is_authenticated():
            return extension.show_not_authenticated_message()

        if len(query) < 3:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='Keep typing for searching in your Vault ...',
                    on_enter=HideWindowAction())
            ])

        return extension.list_passwords(query)


class ItemEnterEventListener(EventListener):
    """ Listener that handles the click on an item """

    # pylint: disable=unused-argument,no-self-use
    def on_event(self, event, extension):
        """ Handles the event """
        data = event.get_data()

        item = extension.lp.get_item(data["id"])

        if re.search("NoteType:Server", item["note"]):

            hostname = re.search("(?<=Hostname:).+?(?=\n)", item["note"]).group(0)
            username = re.search("(?<=Username:).+?(?=\n)", item["note"]).group(0)
            password = re.search("(?<=Password:).+?(?=\n)", item["note"]).group(0)

            return RenderResultListAction([
                ExtensionSmallResultItem(
                    icon='images/icon.png',
                    name='Copy hostname to clipboard for %s' % item["name"],
                    highlightable=False,
                    on_enter=CopyToClipboardAction(hostname),
                ),
                ExtensionSmallResultItem(
                    icon='images/icon.png',
                    name='Copy username to clipboard for %s' % item["name"],
                    highlightable=False,
                    on_enter=CopyToClipboardAction(username),
                ),
                ExtensionSmallResultItem(
                    icon='images/icon.png',
                    name='Copy password to clipboard for %s' % item["name"],
                    highlightable=False,
                    on_enter=CopyToClipboardAction(password),
                )
            ])
            

        if item["is_note"]:
            return RenderResultListAction([
                ExtensionSmallResultItem(
                    icon='images/icon.png',
                    name='Copy note to clipboard',
                    highlightable=False,
                    on_enter=CopyToClipboardAction(item["note"]),
                )
            ])

        return RenderResultListAction([
            ExtensionSmallResultItem(
                icon='images/icon.png',
                name='Copy username to clipboard for %s' % item["name"],
                highlightable=False,
                on_enter=CopyToClipboardAction(item["username"]),
            ),
            ExtensionSmallResultItem(
                icon='images/icon.png',
                name='Copy password to clipboard for %s' % item["name"],
                highlightable=False,
                on_enter=CopyToClipboardAction(item["password"]),
            )
        ])


if __name__ == '__main__':
    LastpassExtension().run()
