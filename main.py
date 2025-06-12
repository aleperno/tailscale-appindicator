#!/usr/bin/env python3

import gi
import os
import multiprocessing
import sys
import dbus
import dbus.mainloop.glib
import subprocess
import time

gi.require_version('Gtk', '3.0')
gi.require_version('AyatanaAppIndicator3', '0.1')
gi.require_version('Notify', '0.7')


from dbus import SessionBus
from gi.repository import Gtk, AyatanaAppIndicator3 as AppIndicator3, Notify, GLib


from persistence import AppIndicatorData, load_data, save_data, enable_sudoers, disable_sudoers
from tailscale import ConnectionStatus, TAILSCALE_RUNNING, TAILSCALE_STOPPED, TAILSCALE_UNKNOWN, TailscaleHandler


Notify.init("MyApp")
BUS_NAME = 'com.example.TailscaleAppIndicator'

BYTE_STATUS_MAPPING = {
    0: ConnectionStatus.UNKNOWN,
    1: ConnectionStatus.DISCONNECTED,
    2: ConnectionStatus.CONNECTED,
    3: ConnectionStatus.LOGGED_OUT,
    4: ConnectionStatus.ERROR,
}

DIR_PATH = os.path.dirname(os.path.realpath(__file__))


dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = SessionBus()


def check_status_worker(write_fd, check_tailscale_status):
    while True:
        status: ConnectionStatus = check_tailscale_status()
        for status_number, _status in BYTE_STATUS_MAPPING.items():
            if status == _status:
                print(f"The result from {status} is : {status_number}")
                os.write(write_fd, status_number.to_bytes(4, 'big'))
        time.sleep(10)


class MyAppIndicator:
    def __init__(self):
        self.indicator = AppIndicator3.Indicator.new(
            "my-simple-indicator",
            #"face-smile",  # use system icon or path to custom icon
            os.path.join(DIR_PATH, "resources/tailscale_main.svg"),
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.current_state = "hello"

        # Set an initial status
        self.connection_status: ConnectionStatus = ConnectionStatus.UNKNOWN

        # Application Data
        self.app_data: AppIndicatorData = load_data()

        # Tailscale Handler
        self.tailscale_handler = TailscaleHandler(sudo_enabled=self.app_data.sudoers_enabled)

        # Set up the menu
        self.menu = Gtk.Menu()

        # Status item
        self.status_item = Gtk.MenuItem(label=f"Status: {self.connection_status.value}")
        self.menu.append(self.status_item)
        self.status_item.set_sensitive(False)

        self.menu.append(Gtk.SeparatorMenuItem())

        # Create a menu item to hold a switch
        self.auto_reconnect_switch = Gtk.CheckMenuItem(label="Auto-Reconnect")
        self.auto_reconnect_switch.set_active(self.app_data.auto_retry)
        self.auto_reconnect_switch.connect("toggled", self.on_toggled_reconnect)
        self.menu.append(self.auto_reconnect_switch)
        self.auto_reconnect_switch.set_sensitive(False)

        self.enable_sudoers_switch = Gtk.CheckMenuItem(label="Enable-Sudoers")
        self.enable_sudoers_switch.set_active(self.app_data.sudoers_enabled)
        self.enable_sudoers_switch.connect("toggled", self.on_toggled_sudoers)
        self.menu.append(self.enable_sudoers_switch)

        # Separator and quit item
        self.menu.append(Gtk.SeparatorMenuItem())

        # Example menu item
        self.item_hello = Gtk.MenuItem(label="Say Hello")
        self.item_hello.connect("activate", self.say_hello)
        #item_hello.show()
        self.menu.append(self.item_hello)

        # Connect Item
        self.connect_item = Gtk.MenuItem(label="Connect")
        self.connect_item.connect("activate", self.connect)
        self.menu.append(self.connect_item)
        self.connect_item.set_sensitive(self.connection_status != ConnectionStatus.CONNECTED)

        # Disconnect Item
        self.disconnect_item = Gtk.MenuItem(label="Disconnect")
        self.disconnect_item.connect("activate", self.disconnect)
        self.menu.append(self.disconnect_item)
        self.disconnect_item.set_sensitive(self.connection_status == ConnectionStatus.CONNECTED)

        # Quit item
        self.item_quit = Gtk.MenuItem(label="Quit")
        self.item_quit.connect("activate", self.quit)
        self.menu.append(self.item_quit)

        #self.item_quit.set_sensitive(False)


        self.menu.show_all()
        self.indicator.set_menu(self.menu)

        # Once the menu has been defined, update the status
        self.update_connection_status()


        ###### Worker Variables #####
        # Pipe creation
        self.read_fd, self.write_fd = os.pipe()
        # Worker Variable
        self.proc = None
        # Add watcher
        GLib.io_add_watch(self.read_fd, GLib.IO_IN, self.callback)

        # Start Worker ony if the current status is Connected, otherwise it will be in vain
        if self.connection_status == ConnectionStatus.CONNECTED:
            self.start_worker()

    def start_worker(self):
        if not self.proc:
            self.proc = multiprocessing.Process(target=check_status_worker,
                                                args=(self.write_fd, self.tailscale_handler.check_status))
            self.proc.start()

    def terminate_worker(self):
        if self.proc:
            self.proc.terminate()
            self.proc = None

    def on_toggled_reconnect(self, item):
        state = item.get_active()
        self.app_data.auto_retry = state
        save_data(self.app_data)
        print("Feature is ON" if state else "Feature is OFF")

    def on_toggled_sudoers(self, item):
        new_state = item.get_active()
        if new_state:
            # we want to enable sudoers
            item.set_active(enable_sudoers())
        else:
            # We want to disable sudoers
            item.set_active(not disable_sudoers())

        state = item.get_active()
        self.app_data.sudoers_enabled = state
        self.tailscale_handler.sudo_enabled = state
        save_data(self.app_data)
        print("Feature is ON" if state else "Feature is OFF")

    def callback(self, fd, condition):
        try:
            status_int = int.from_bytes(os.read(fd, 4), 'big')
            print(f"Data es {status_int}")
            new_status: ConnectionStatus = BYTE_STATUS_MAPPING[status_int]
            old_status = self.connection_status
            self.connection_status = new_status
            self.refresh_connection_status()
            self.check_disconnection(old_status)
        except:
            pass
        return True

    def check_disconnection(self, old_state: ConnectionStatus):
        if old_state == ConnectionStatus.CONNECTED and self.connection_status != old_state:
            self.notify_disconnection()

    def notify_disconnection(self):
        notification = Notify.Notification.new("TailScale Disconnected",
                                               f"Auto reconnect is {'' if self.app_data.auto_retry else 'NOT '}ON")
        notification.show()
        # Play the system sound
        subprocess.Popen(["canberra-gtk-play", "--id", "message-new-instant"])

    def say_hello(self, _):
        if self.current_state == 'hello':
            notification = Notify.Notification.new("Hello!", "This is a desktop notification.")
            self.item_hello.set_label('Say Bye')
            self.current_state = 'bye'
        else:
            notification = Notify.Notification.new("Bye!", "This is a desktop notification.")
            self.item_hello.set_label('Say Hello')
            self.item_quit.set_sensitive(True)
        notification.show()
        # Play the system sound
        subprocess.Popen(["canberra-gtk-play", "--id", "message-new-instant"])
        #self.menu.show_all()

    def connect(self, _):
        self.tailscale_handler.connect()
        self.update_connection_status()
        if self.connection_status == ConnectionStatus.CONNECTED:
            # We should start checking the status
            self.start_worker()

    def disconnect(self, _):
        if self.connection_status == ConnectionStatus.CONNECTED:
            self.tailscale_handler.disconnect()
        self.update_connection_status()
        self.terminate_worker()

    def update_connection_status(self):
        self.connection_status = self.tailscale_handler.check_status()
        self.refresh_connection_status()

    def refresh_connection_status(self):
        self.status_item.set_label(label=f"Status: {self.connection_status.value}")
        icon = 'tailscale_connected.svg' if self.connection_status == ConnectionStatus.CONNECTED else 'tailscale_disconnected.svg'
        self.indicator.set_icon_full(os.path.join(DIR_PATH, f"resources/{icon}"), "Foo")
        self.connect_item.set_sensitive(self.connection_status != ConnectionStatus.CONNECTED)
        self.disconnect_item.set_sensitive(self.connection_status == ConnectionStatus.CONNECTED)

    def quit(self, _):
        Gtk.main_quit()
        self.terminate_worker()


def main():
    try:
        result = bus.request_name(BUS_NAME, dbus.bus.NAME_FLAG_DO_NOT_QUEUE)
        if result != dbus.bus.REQUEST_NAME_REPLY_PRIMARY_OWNER:
            print("Another instance is already running.")
            sys.exit(1)
    except dbus.DBusException:
        sys.exit(1)

    MyAppIndicator()
    Gtk.main()


if __name__ == "__main__":
    main()
