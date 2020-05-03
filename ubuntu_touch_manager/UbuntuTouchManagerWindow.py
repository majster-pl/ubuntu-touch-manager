# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2013 Szymon Waliczek majsterrr@gmail.com
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License version 3, as published 
# by the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along 
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

from locale import gettext as _

from gi.repository import Gtk, GdkPixbuf, GObject # pylint: disable=E0611
from gi.repository.GdkPixbuf import Pixbuf
import logging
import commands # for os output
import xdg.BaseDirectory # module needed for determing user default directorys
import ConfigParser # module for reading and writing config file
import Image # for resizing, rotating etc pictures...
import shutil # copping files module
import string

import subprocess
from subprocess import *
import time
import os
from threading import Thread
GObject.threads_init()

logger = logging.getLogger('ubuntu_touch_manager')

from ubuntu_touch_manager_lib import Window
from ubuntu_touch_manager.AboutUbuntuTouchManagerDialog import AboutUbuntuTouchManagerDialog
from ubuntu_touch_manager.PreferencesUbuntuTouchManagerDialog import PreferencesUbuntuTouchManagerDialog


app_name = "Ubuntu-Touch-Manager"
user_dir = os.path.expanduser('~')
ubuntuone_dir = user_dir + "/Ubuntu One/public/"
dropbox_dir = user_dir + "/Dropbox/Public/Ubuntu-touch-manager/"
img_folder = "/home/szymon/Desktop/"
config_dir = os.path.join(xdg.BaseDirectory.xdg_config_home, app_name)
config = os.path.join(xdg.BaseDirectory.xdg_config_home, app_name, app_name + ".conf")
app_dir = "/usr/share/ubuntu-touch-manager/ui/"



# See ubuntu_touch_manager_lib.Window.py for more details about how this class works
class UbuntuTouchManagerWindow(Window):
    __gtype_name__ = "UbuntuTouchManagerWindow"
    
    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(UbuntuTouchManagerWindow, self).finish_initializing(builder)

        self.AboutDialog = AboutUbuntuTouchManagerDialog
        self.PreferencesDialog = PreferencesUbuntuTouchManagerDialog

        # Code for other initialization actions should be added here.
        self.toolbar_main = self.builder.get_object("toolbar_main")
        context = self.toolbar_main.get_style_context()
        context.add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)
        ### Status
        self.status_label = self.builder.get_object("status_label")
        self.status_image = self.builder.get_object("status_image")

        ### Buttons
        self.toolbutton_connect = self.builder.get_object("toolbutton_connect")
        self.toolbutton_screenshot = self.builder.get_object("toolbutton_screenshot")
        self.toolbutton_screenshot_handler_id = self.toolbutton_screenshot.connect("toggled", self.toolbutton_screenshot_toggled)
        self.toolbutton_download = self.builder.get_object("toolbutton_download")
        self.toolbutton_download_handler_id = self.toolbutton_download.connect("toggled", self.toolbutton_download_toggled)
        self.toolbutton_send = self.builder.get_object("toolbutton_send")
        self.toolbutton_send_handler_id = self.toolbutton_send.connect("toggled", self.toolbutton_send_toggled)
        self.toolbutton_advanced = self.builder.get_object("toolbutton_advanced")
        self.toolbutton_advanced_handler_id = self.toolbutton_advanced.connect("toggled", self.toolbutton_advanced_toggled)
        ## test button
        self.toolbutton_test = self.builder.get_object("toolbutton_test")

        self.toolbutton_screenshot.set_sensitive(False)
        self.toolbutton_download.set_sensitive(False)
        self.toolbutton_send.set_sensitive(False)
        self.toolbutton_advanced.set_sensitive(False)

        ### Select folder for screenshots dialog
        self.dialog_select_folder = self.builder.get_object("dialog_select_folder")
        self.button_cancel_dialog = self.builder.get_object("button_cancel_dialog")
        self.button_ok_dialog = self.builder.get_object("button_ok_dialog")
        self.filechooserbutton1 = self.builder.get_object("filechooserbutton1")

        ### Select folder for download files
        self.dialog_select_download_folder = self.builder.get_object("dialog_select_download_folder")
        self.button_cancel_download_folder = self.builder.get_object("button_cancel_download_folder")
        self.button_ok_download_folder = self.builder.get_object("button_ok_download_folder")

        ### Creating config dir
        self.dir_creator(config_dir)

        ### Main window boxes and main image/logo
        self.box_download = self.builder.get_object("box_download")
        self.box_send = self.builder.get_object("box_send")
        self.box_screenshot = self.builder.get_object("box_screenshot")
        self.box_advanced = self.builder.get_object("box_advanced")
        self.image_screenshot = self.builder.get_object("image_screenshot")
        self.image_logo = self.builder.get_object("image_logo")
        self.toolbar_picture = self.builder.get_object("toolbar_picture")

        ### widgets in pictures tab
        self.button_capture = self.builder.get_object("button_capture")
        self.button_open = self.builder.get_object("button_open")
        self.button_share = self.builder.get_object("button_share")
        self.button_delete = self.builder.get_object("button_delete")
        self.button_screenshot_settings = self.builder.get_object("button_screenshot_settings")
        self.button_open.set_sensitive(False)
        self.button_share.set_sensitive(False)
        self.button_delete.set_sensitive(False)
        self.box_link = self.builder.get_object("box_link")
        self.toolbutton_copy_url = self.builder.get_object("toolbutton_copy_url")
        self.image_cloud_screenshot = self.builder.get_object("image_cloud_screenshot")



        ### widgets in Download tab
        self.radio_pictures = self.builder.get_object("radio_pictures")
        self.radio_pictures.connect("toggled", self.on_radio_toggled, "Pictures")
        self.download_src = "/data/ubuntu/home/phablet/Pictures/"
        self.progressbar_download = self.builder.get_object("progressbar_download")
        self.filechooserbutton_download = self.builder.get_object("filechooserbutton_download")
        self.radio_downloads = self.builder.get_object("radio_downloads")
        self.radio_downloads.connect("toggled", self.on_radio_toggled, "Downloads")
        self.radio_videos = self.builder.get_object("radio_videos")
        self.radio_videos.connect("toggled", self.on_radio_toggled, "Videos")
        self.radio_music = self.builder.get_object("radio_music")
        self.radio_music.connect("toggled", self.on_radio_toggled, "Music")
        self.radio_custom = self.builder.get_object("radio_custom")
        self.radio_custom.connect("toggled", self.on_radio_toggled, "custom")
        ##
        self.box6 = self.builder.get_object("box6")
        self.button4 = self.builder.get_object("button4")
        self.button_download = self.builder.get_object("button_download")

        self.entry_custom_download = Gtk.Entry()
        self.box6.pack_start(self.entry_custom_download, True, True, 0)
#        self.entry_custom_download.set_sensitive(False)
        self.entry_custom_download.set_placeholder_text("/home/phablet/<folder or file name>")
        self.entry_custom_download.connect("changed", self.entry_custom_download_changed)
        self.entry_custom_download.connect("button-press-event", self.entry_custom_download_press_event)

        self.entry_custom_download.show()

        ### widgets in Upload tab
        self.button_upload = self.builder.get_object("button_upload")
        self.filechooserbutton_upload = self.builder.get_object("filechooserbutton_upload")
        self.progressbar_upload = self.builder.get_object("progressbar_upload")


        ### Adding menu for editing images and adding installed apps on the system to the menu.
        self.menu = Gtk.Menu()
        self.menu.get_style_context().add_class('popup') # applying before created class .popup 
        app_list = ["dropbox", "ubuntuone"] # list of programs for editing photos
        for i in app_list:
            img = Gtk.Image()
            menu_item = Gtk.ImageMenuItem(i)
            menu_item.set_name("Image_edit")
            icons_path = app_dir + i + ".png"
            img = img.new_from_file(icons_path)
            menu_item.set_image(img)
            menu_item.set_always_show_image(True)
            menu_item.connect("activate", self.menuitem_response, i, True)
            menu_item.show()
            self.menu.append(menu_item)



################################################## CONFIG FILE ############################################################
#
        self.config = ConfigParser.ConfigParser()
        self.config.read(config)
        if os.path.isfile(config):
            # config exists, then read config in to app, available vars: self.server_active, self.dropbox_dir_set, self.ubuntuone_dir_set
            self.configuration_reading()
        else:
            # config is missing, creat new config with default values
            print "Welcome to %s! " % app_name
            self.config.add_section('Options')
            self.config.set('Options', 'screenshot_dir', '')
            with open(config, 'wb') as configfile:
                self.config.write(configfile)
        output = commands.getoutput('which %s' % "adb")
        self.show()
        if output:
            print "adb installed [ OK ]"
            self.connect_thread()
        else:
            print "adb NOT installed [ NO ]"
            self.adb_check()


######### CODE BELOW ##########
    def configuration_reading(self):
        cfg = str(config)
        self.config.read(cfg)
        self.screenshot_dir = self.config.get('Options', 'screenshot_dir')


#####################  TEST CODE ########################
##

        self.progressbar_upload.set_show_text(True)
        self.progressbar_upload.set_text(None)


##
###############// END // TEST CODE // END // #############

############### THREADS ###############
##
    def connect_thread(self):
        Thread(target=self.connect_test).start()

    def adb_thread(self):
        Thread(target=self.adb_check).start()

    def download_thread(self, download_folder):
        Thread(target=self.downloading_files, args=(download_folder,)).start()

    def upload_thread(self):
        Thread(target=self.upload_bar).start()

    def screenshot_thread(self):
        Thread(target=self.capture).start()

##
####### /// END /// THREADS /// END /// ###############


################ TOOLBAR_MAIN #########
##
    def toolbattons_sens(self, sens):
        self.toolbutton_screenshot.set_sensitive(sens)
        self.toolbutton_download.set_sensitive(sens)
        self.toolbutton_send.set_sensitive(sens)
        self.toolbutton_advanced.set_sensitive(sens)
##
###########  // END // TOOLBAR_MAIN // END //  #########



############## Hiding all boxes in main window ( when button in toolbar toggled ) #######
##
    def buttons_state_res(self):
        self.box_send.hide()
        self.toolbutton_send.handler_block(self.toolbutton_send_handler_id)
        self.toolbutton_send.set_active(False)
        self.toolbutton_send.handler_unblock(self.toolbutton_send_handler_id)

        self.box_download.hide()
        self.toolbutton_download.handler_block(self.toolbutton_download_handler_id)
        self.toolbutton_download.set_active(False)
        self.toolbutton_download.handler_unblock(self.toolbutton_download_handler_id)

        self.box_screenshot.hide()
        self.toolbutton_screenshot.handler_block(self.toolbutton_screenshot_handler_id)
        self.toolbutton_screenshot.set_active(False)
        self.toolbutton_screenshot.handler_unblock(self.toolbutton_screenshot_handler_id)

        self.box_advanced.hide()
        self.toolbutton_advanced.handler_block(self.toolbutton_advanced_handler_id)
        self.toolbutton_advanced.set_active(False)
        self.toolbutton_advanced.handler_unblock(self.toolbutton_advanced_handler_id)
##
### // END // #### Hiding all boxes in main window ( when button in toolbar toggled ) ## // END // ###


    def adb_check(self):
        print "testing adb..."
        output = commands.getoutput('which %s' % "adb")
        if output:
            print "adb installed [ OK ]"
        else:
            print "adb installed [ NO ]"
            # sudo add-apt-repository ppa:phablet-team/tools

            dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.QUESTION,
                Gtk.ButtonsType.YES_NO)
            dialog.set_title("Package missing!")
            dialog.set_markup("<big><b>Do you want to install?</b></big>\n\n"
                            "In order to use Ubuntu Touch Manager you need to have <b>android-tools-adb</b> installed.\n\n"
                            "Click <b>Yes</b> to install it now\n"
                            "<i>(terminal window will open and you will be asked to provide root password)</i>\n"
                            "<b>or</b>\n"
                            "Click <b>No</b> and install it manually fallowing instructions on this website"
                            " <a href=\"https://wiki.ubuntu.com/Touch/Install\" "
                            "title=\"Click to find out more\">https://wiki.ubuntu.com/Touch/Install</a> and then run aplication again.")

            response = dialog.run()
            # On button YES clicked dialog will be destroyed.
            if response == Gtk.ResponseType.YES:
                # Set focus at entry_add_url box
#                self.entry_add_url.grab_focus()
                print "Respond OK"
                if os.path.isfile("/etc/apt/sources.list.d/phablet-team-tools-raring.list"):
                    print "ppa already added!"
                    os.system("gnome-terminal -e 'bash -c \"sudo apt-get install android-tools-adb -y\"'")
                    self.adb_check_after()
                else:
                    print "new ppa will be added during instalation:  \"ppa:phablet-team/tools\""
                    os.system("gnome-terminal -e 'bash -c \"sudo add-apt-repository ppa:phablet-team/tools -y && sudo apt-get update && sudo apt-get install android-tools-adb -y\"'")
                    self.adb_check_after()
            # On button YES clicked dialog will be destroyed.
            elif response == Gtk.ResponseType.NO:
                print "\n\n\nPlease install android-tools-adb manually and run Ubuntu Touch Manager again.\nExiting now..."
                dialog.destroy()
                self.status_bar_update("Starting adb server Error! (not installed)", Gtk.STOCK_STOP)
                return
            dialog.destroy()
            


    def adb_check_after(self):
        output = commands.getoutput('which %s' % "adb")
        if output:
            print "adb installed [ OK ]"

            dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO,
                Gtk.ButtonsType.OK)
            dialog.set_title("Installation completed!")
            dialog.set_markup("<big><b>Installation completed!</b></big>\n\n"
                            "Package <b>android-tools-adb</b> has been installed correctly.")
            self.connect_thread()
            dialog.run()
            dialog.destroy()

        else:
            print "adb installed [ NO ]"
            dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR,
                Gtk.ButtonsType.CLOSE)
            dialog.set_title("Instalation ERROR!")
            dialog.set_markup("<big><b>Installation ERROR!</b></big>\n\n"
                            ""
                         "Something went wrong during instalation of <b>android-tools-adb</b>.\n"
                         "Please install android-tools-adb manually and run Ubuntu Touch Manager again.\n\n"
                         "<i>For more info <b>how to install</b> android-tools-adb on your\nUbuntu machine, click on link below and go to \"Step 1 - Desktop Setup\"</i>\n"
                         "<a href=\"https://wiki.ubuntu.com/Touch/Install\" "
                         "title=\"Click to find out more\">https://wiki.ubuntu.com/Touch/Install</a>")
            self.status_bar_update("Starting adb server Error! (not installed)", Gtk.STOCK_STOP)
            dialog.run()
            dialog.destroy()




    def connect_test(self):
        cmd = 'ps aux'
        status, output = commands.getstatusoutput(cmd)
        if string.find( output, "adb") > -1:
            print "adb running [ OK ]"
            self.status_bar_update("ready", Gtk.STOCK_OK)
        else:
            print "adb running [ NO ]"
            print "\n\n\Starting adb server..."
            self.status_bar_update("Starting adb server...", Gtk.STOCK_REFRESH)
            os.system("adb start-server")
            time.sleep(2)
            status, output = commands.getstatusoutput(cmd)
            if string.find( output, "adb") > -1:
                print "adb running [ OK ]"
                self.status_bar_update("ready", Gtk.STOCK_OK)
            else:
                print "adb running [ NO ]"
                self.status_bar_update("Starting adb server Error!", Gtk.STOCK_OK_STOP)

            

    def on_toolbutton_test_clicked(self, widget):
        print "button test"
        self.filechooserbutton_upload.set_select_multiple(True)




########################### Box_screenshot content #########################
##

    def on_button_capture_clicked(self, widget):
        try: self.link_button
        except:
            print "Nie ma self.link_button"
        else:
            self.box_link.remove(self.link_button)
            self.box_link.hide()

        self.configuration_reading()
        if self.screenshot_dir != "":
            self.screenshot_thread()
        else:
            print "Please select where you want me to save your screenshots..."
            self.dialog_select_folder.show()


        

 #Button capture clicked
    def capture(self):

        print "Taking screenshot of your device..."
        self.status_bar_update("Taking screenshot...", Gtk.STOCK_REFRESH)
        cur_time = time.ctime()
        img_name = "Screenshot from " + cur_time + ".png"
        adb_output = commands.getoutput('adb shell /system/bin/screencap -p /sdcard/screenshot.png')
        # Taking screenshot and saving on device...
        self.configuration_reading()
        adb_output = commands.getoutput('adb pull /sdcard/screenshot.png %s/%s' % ( self.screenshot_dir, img_name.replace(" ","\\ ")) )
        # Pulling screenshot from device to user directory...

        img_dir = self.screenshot_dir + "/" + img_name
        self.current_pic_path = img_dir
        self.current_pic_name = img_name
        pixbuf_pic = GdkPixbuf.Pixbuf.new_from_file_at_size(str(img_dir), 280, 280)
        self.image_screenshot.set_from_pixbuf(pixbuf_pic)
        self.image_screenshot.show()
        self.toolbar_picture.show()
        self.status_bar_update("Taking screenshot... Done", Gtk.STOCK_OK)
        self.button_open.set_sensitive(True)
        self.button_share.set_sensitive(True)
        self.button_delete.set_sensitive(True)
        #self.image_screenshot.set_from_file("%s/%s" % (self.screenshot_dir, img_name) )
#        subprocess.call(["xdg-open", "%s/%s" % (self.screenshot_dir, img_name)])


 #Button Delete clicked
    def on_button_delete_clicked(self, widget):
        print "Button delete picture clicked."
        try: self.link_button
        except:
            print "Nie ma self.link_button"
        else:
            self.box_link.remove(self.link_button)
        # deleting picture from folder selected before by user
        shutil.os.remove(self.current_pic_path)
        #hiding image
        self.image_screenshot.hide()
        self.button_open.set_sensitive(False)
        self.button_share.set_sensitive(False)
        self.button_delete.set_sensitive(False)

 #Button Open clicked
    def on_button_open_clicked(self, widget):
        print "Button Open folder clicked."
        os.system('xdg-open "%s"' % self.screenshot_dir)

 #Button Share cicked
    def on_button_share_clicked(self, widget):
        print "Button share clicked."
        self.menu.popup(None, None, None, None, 0, 0)
        self.menu.show_all()

    def menuitem_response(self, widget, string):
        app = string
        try: self.link_button
        except:
            print "Nie ma self.link_button"
        else:
            self.box_link.remove(self.link_button)
            self.box_link.hide()
#        print string
        if string == "dropbox":
            print "\n\n-----------------------\n *Checking Dropbox...*\n-----------------------"
            output = commands.getoutput("which dropbox")
            if output:
                print "- Dropbox is installed"
                output = commands.getoutput("dropbox status")
                if "Dropbox isn't running" in output:
                    print "- Dropbox isn't running"
                    self.dialog_error("Dropbox isn't running", "Please run Dropbox and then try again.")
                    return

                elif "Syncing paused" in output:
                    print "- Dropbox syncing paused!"
                    self.dialog_error("Dropbox is poused!", "Please <b>unpouse</b> syncing and then try again.")
                    return

                elif "Waiting to be linked" in output:
                    print "- Dropbox is Waiting to be linked to an account..."
                    self.dialog_error("Dropbox is Not linked!", "Please setup your Dropbox account and then try again.")
                    return

                elif "Downloading" in output or "Updating" in output or "Indexing" in output:
                    print "- Dropbox is syncing..."
                    self.dialog_info("Dropbox is busy.", "It looks like you uploading or downloading something to/from Dropbox.\n"
                                        "It's only mean, that link might not be available online straightaway.")

                elif "Idle" in output:
                    print "- Dropbox is Idling - ready"

                else:
                    print "Unknown error occurred!\nOperation aborted."
                    self.dialog_error("Unknown error occurred!", "Operation aborted.")
                    return

            else:
                print "- Dropbox NOT installed"
                self.dialog_error("Dropbox not installed!", "Please install Dropbox and setup your dropbox account.\nThen try again.")
                return
            self.dir_creator(dropbox_dir)
            dropbox_pic_dir = os.path.join(dropbox_dir,self.current_pic_name)
            shutil.copy2(self.current_pic_path, dropbox_pic_dir)
            command = 'dropbox puburl %s' % dropbox_pic_dir.replace(" ","\\ ")
            url = commands.getoutput(command)
            print url
            self.pic_url = url
            self.link_button = Gtk.LinkButton(url, self.current_pic_name)
            self.box_link.add(self.link_button)
            self.image_cloud_screenshot.set_from_file(app_dir + "dropbox.png")
            self.box_link.show_all()


        if string == "ubuntuone":
            ubuntuone_state = commands.getoutput('u1sdtool -s | grep "is_connected"')
            if "True" in ubuntuone_state:
                print "Ubuntu One is conncected"
            else:
                print "UbuntuOne NOT connected!"
                self.dialog_error("Ubuntu One Error!", "Please make sure your Ubuntu One account is set up and internet " 
                                    "connection is estabished!\nThen try again.")
                return
            print "sending picture to ubuntu one"
            u1_pic_dir = os.path.join(ubuntuone_dir,self.current_pic_name)
            shutil.copy2(self.current_pic_path, u1_pic_dir)
            time.sleep(2)
            command = 'u1sdtool --publish-file %s' % u1_pic_dir.replace(" ","\\ ")
            fin, fout = os.popen4(command)
            result = fout.read()
            url_position = result.find('http')
            url = result[url_position:]
            print url
            self.pic_url = url
            self.link_button = Gtk.LinkButton(url, self.current_pic_name)
            self.box_link.add(self.link_button)
            self.image_cloud_screenshot.set_from_file(app_dir + "ubuntuone.png")
            self.box_link.show_all()

 #Def for displaying error message
    def dialog_error(self, title, text):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR,
            Gtk.ButtonsType.OK)
        dialog.set_title("Error")
        dialog.set_markup("<big><b>" + str(title) + "</b></big>\n\n"
                            "" + str(text) + "")
        dialog.run()
        dialog.destroy()

 #Def for displaying info message
    def dialog_info(self, title, text):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO,
            Gtk.ButtonsType.OK)
        dialog.set_title("Info")
        dialog.set_markup("<big><b>" + str(title) + "</b></big>\n\n"
                            "" + str(text) + "")
        dialog.run()
        dialog.destroy()

 #Button toolbutton_copy_url cliked
    def on_toolbutton_copy_url_clicked(self, widget):
        cmd = "echo -n '%s' | xclip -selection c" % self.pic_url
        os.system(cmd)
        print self.pic_url + " Copied to clipboard"


 #Button button_screenshot_settings
    def on_button_screenshot_settings_clicked(self, widget):
        self.dialog_select_folder.show()


  ##################### Buttons on dialog_select_folder  #####################
 #@
    # button cancel
    def on_button_cancel_dialog_clicked(self, widget):
        self.dialog_select_folder.hide()
        return True
    # button ok
    def on_button_ok_dialog_clicked(self, widget):
        dir_choosen = self.filechooserbutton1.get_filename()

        self.config.set('Options', 'screenshot_dir', dir_choosen)
        with open(config, 'wb') as configfile:
            self.config.write(configfile)
        self.dialog_select_folder.hide()
        return True
    # destroy event for dialog_select_folder
    def on_dialog_select_folder_delete_event(self, widget, data=None):
        self.dialog_select_folder.hide()
    	return True
 #@
  ##################### /// END /// Buttons on dialog_select_folder /// END ///  ##############


##
########################### /// END /// Box_screenshot content /// END /// #########################



########################### Box_download content #########################
##
 #Radio button changed
    def on_radio_toggled(self, widget, name):
        if name == "custom":
            print "custom folder to be choosed..."
            self.entry_custom_download.set_sensitive(True)
#            self.entry_custom_download.set_editable(True)

        else:
            self.download_src = "/data/ubuntu/home/phablet/%s/" % name
#            self.entry_custom_download.set_editable(False)
            self.entry_custom_download.set_sensitive(False)
            print self.download_src


    def entry_custom_download_changed(self, widget):
        text = self.entry_custom_download.get_text()
        if text[-1:] == "/":
            ls_dir = "/data/ubuntu" + text
            self.ls_menu(ls_dir)
        else:
            print ".."


    def entry_custom_download_press_event(self, widget, event):
        self.radio_custom.set_active(True)
        try: self.menu_ls
        except:
            pass
        else:
            self.menu_ls.popup(None, None, None, None, 0, 0)
            self.menu_ls.show_all()


    def ls_menu(self, ls_dir):
        self.menu_ls = Gtk.Menu()
        img = Gtk.Image()
        lista_dir = 'adb shell "ls -l %s"' % ls_dir
        status2, output2 = commands.getstatusoutput(lista_dir)
        list_ls = output2.splitlines()

        for i in list_ls:
            if "d" in i[0]:
                print "FOLDER"
                icons_path = "/usr/share/icons/gnome/scalable/places/folder-symbolic.svg"
                menu_item = Gtk.ImageMenuItem(i.split()[-1])
                img = img.new_from_file(icons_path)
                menu_item.set_image(img)
                menu_item.set_always_show_image(True)
                menu_item.connect("activate", self.menuitem_response, i.split()[-1], True)
                menu_item.show()
                self.menu_ls.append(menu_item)

        for i in list_ls:
            if "-" in i[0]:
                print "File!"
                menu_item = Gtk.ImageMenuItem(i.split()[-1])
                icons_path = "/usr/share/icons/gnome/scalable/emblems/emblem-documents-symbolic.svg"
                img = img.new_from_file(icons_path)
                menu_item.set_image(img)
                menu_item.set_always_show_image(True)
                menu_item.connect("activate", self.menuitem_response, i.split()[-1], False)
                menu_item.show()
                self.menu_ls.append(menu_item)


    def on_button4_clicked(self, widget):
        self.menu_ls.popup(None, None, None, None, 0, 0)
        self.menu_ls.show_all()

    def menuitem_response(self, widget, name, lol):
        print name
        text = self.entry_custom_download.get_text()
        while text[-1] != "/":
            self.entry_custom_download.set_text(text[:-1])
            text = self.entry_custom_download.get_text()

        if lol == True:
            new_dir = text + name + "/"
            self.entry_custom_download.set_text(new_dir)

        elif lol == False:
            new_dir = text + name
            self.entry_custom_download.set_text(new_dir)


    def files_count(self):
        folder_names = ["Pictures", "Downloads", "Videos", "Music"]
        for i in folder_names:
            print i
            path = "/data/ubuntu/home/phablet/%s/" % i
            cmd = 'adb shell "ls %s" | grep -c ""' % path
            status, output = commands.getstatusoutput(cmd)
            if int(output) == 1:
                label = "%s  ( /home/phablet/%s )  (%s file)" % (i, i, str(output))
            elif int(output) > 1:
                label = "%s  ( /home/phablet/%s )  (%s files)" % (i, i, str(output))
            elif int(output) == 0:
                label = "%s  ( /home/phablet/%s )  (0 files)" % (i, i)
            button = "radio_" + i.lower()
            vars(self)[button].set_label(label)

 #Button Download clicked
    def on_button_download_clicked(self, widget):
        print "Downloading:  %s" % self.download_src
        os.system('adb root')
        self.dialog_select_download_folder.show()

 #Downloading thread function
    def downloading_files(self, download_folder):
        self.progressbar_download.set_fraction(0.0)
        print "downloading files...."        
        download_src = self.download_src
        cmd = 'adb shell "ls %s" | grep -c ""' % self.download_src
        status, output = commands.getstatusoutput(cmd)
        lista = 'adb shell "ls %s"' % download_src
        status2, output2 = commands.getstatusoutput(lista)
        downloaded = 0
        list_test = output2.splitlines()
        if int(output) == 1:
            path = download_src
            os.system('cd %s && adb pull "%s"' % (download_folder, path) )
            self.progressbar_download.set_fraction(1)
        #else
        else:
            for i in list_test:
                print i
                path = download_src + i
                os.system('cd %s && adb pull "%s"' % (download_folder, path) )
                fraction = (int(downloaded) / float(output))
                self.progressbar_download.set_fraction(fraction)
                downloaded += 1
            self.progressbar_download.set_fraction(1)


  ##################### Dialog file chooser #######################
 #@
    #Button OK in dialog_select_download_folder
    def on_button_ok_download_folder_clicked(self, widget):
        dir_choosen = self.filechooserbutton_download.get_filename()
        print dir_choosen
        self.dialog_select_download_folder.hide()
        if self.radio_custom.get_active() == True:
            print "custom loacation seleceted..."
            self.download_src = "/data/ubuntu"+self.entry_custom_download.get_text()
        else:
            pass
        self.download_thread(dir_choosen)
    	return True

    #Button Cancel in dialog_select_download_folder
    def on_button_cancel_download_folder_clicked(self, widget):
        self.dialog_select_download_folder.hide()
    	return True

    #Destroy event for dialog_select_download_folder
    def on_dialog_select_download_folder_delete_event(self, widget, data=None):
        self.dialog_select_download_folder.hide()
    	return True
 #@
  ############ /// END  Dialog file chooser /// END /// ################

##
########################### /// END /// Box_download content /// END /// #########################



############################ Box_send content ######################
##

    def on_filechooserbutton_upload_file_set(self, widget):
        print "test working!"
        self.progressbar_upload.set_fraction(0)
        self.progressbar_upload.set_text(None)

    def on_button_upload_clicked(self, widget):
        self.progressbar_upload.pulse()
        src_file = self.filechooserbutton_upload.get_filename()
        upload_dir = "/data/ubuntu/home/phablet/Uploads/"
#        upload_dir = "/sdcard/Download/lol"
        cmd = 'adb shell "ls %s"' % upload_dir
        status, output = commands.getstatusoutput(cmd)
        if string.find( output, "No such file or directory") > -1:
            print "\n\nMissing folder: %s \nCreating forder %s" % (upload_dir, upload_dir)
            os.system("adb shell mkdir %s" %upload_dir)
            self.uploading_file(src_file, upload_dir)
        else:
            print "Folder pressent"
            self.uploading_file(src_file, upload_dir)


    def uploading_file(self, src_file, upload_dir):
        print "Uploading file to your device..."
#        adb push /home/szymon/Downloads/cm-10.1-20130422-NIGHTLY-mako.zip /sdcard/Download/test.zip        
        cmd = "adb push " + src_file.replace(" ","\\ ").replace("(","\\(").replace(")","\\)") + " " + upload_dir.replace(" ","\\ ") + " && touch /tmp/UTM.upload"
        print cmd
        self.cmd2 = cmd
        self.status_bar_update("Uploading file...", Gtk.STOCK_REFRESH)
        self.upload_thread()

    # uploading file fo device
    def upload_bar(self):
        stream = os.popen(self.cmd2)
        while not os.path.isfile("/tmp/UTM.upload"):
            print "Uploading..."
            self.progressbar_upload.pulse()
            self.progressbar_upload.set_text("Uploading...")
            time.sleep(0.2)
        print "Upload Complited"
        self.progressbar_upload.set_fraction(1)
        self.progressbar_upload.set_text("Done")
        os.system("rm /tmp/UTM.upload")
        self.status_bar_update("File Uploaded.", Gtk.STOCK_OK)

    def upload_button_sens(self):
        if self.filechooserbutton_upload.get_file() != None:
            print self.filechooserbutton_upload.get_file()
            self.button_upload.set_sensitive(True)
        else:
            print "No file set!"
            self.button_upload.set_sensitive(False)

##
############## // END // Box_send content // END //  #################




################# status bar function ##############
##

    def status_bar_update(self, text, icon):
        print "changing status bar status..."
        #self.status_image.set_from_stock(Gtk.STOCK_OK, 3)
        self.status_image.set_from_stock(icon, 2)
        self.status_label.set_text(text)
##
########## // END // status bar function // END // ##############


##################################### Main Toolbar buttons  ######################################
##


 ### Connect Button clicked
    def on_toolbutton_connect_clicked(self, widget):
        output = commands.getoutput('which %s' % "adb")
        if output:
            print "adb installed [ OK ]"
        else:
            print "adb installed [ NO ]"
            self.status_image.set_from_stock(Gtk.STOCK_STOP, 2)
            self.status_label.set_text("Starting adb server Error! (not installed)")
            dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR,
                Gtk.ButtonsType.CLOSE)
            dialog.set_title("adb missing!")
            dialog.set_markup("<big><b>android-tools-adb missing!</b></big>\n\n"
                         "Please install android-tools-adb manually and run Ubuntu Touch Manager again.\n\n"
                         "<i>For more info <b>how to install</b> android-tools-adb on your\nUbuntu machine, click on link below and go to \"Step 1 - Desktop Setup\"</i>\n"
                         "<a href=\"https://wiki.ubuntu.com/Touch/Install\" "
                         "title=\"Click to find out more\">https://wiki.ubuntu.com/Touch/Install</a>")
            dialog.run()
            dialog.destroy()
            return
        
        self.buttons_state_res()
        self.toolbattons_sens(False) #setting sensitivity of the toolbuttons to False
        self.status_bar_update("Device NOT connected!", Gtk.STOCK_STOP)
        adb_output = commands.getoutput('adb devices | tail -n+2')
        if adb_output != "":
            print "Device detected"
            if "device" in adb_output:
                print "Connected"
                self.status_bar_update("Device Connected!", Gtk.STOCK_OK)
                self.toolbattons_sens(True)
            else:
                print "Not connected, click ok on the phone."
                # No device detected meassage
                dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR,
                    Gtk.ButtonsType.OK)
                dialog.set_markup("<big><b>USB Debuging!</b></big>\n\n"
                                "Please accept USB Debuging on your mobile device.\n\n\n\n"
                                "<b>[Troubleshooting]</b>\n"
                                "In terminal enter \"adb devices\" and see if your device is listed there.\n"
                                "Output of \"adb devices\"should looks like this:\n"
                                "$ List of devices attached\n"
                                "$ 003fd0755a4a11ff	<b>device</b>\n\n"
                                "Not like this:\n"
                                "$ List of devices attached\n"
                                "$ 003fd0755a4a11ff	<b>offline</b>")
    
                dialog.run()
                dialog.destroy()
                
        else:
            print "Device not detevted"
            # No device detected meassage
            dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK)
            dialog.set_markup("<big><b>No device detected!</b></big>\n\n"
                            "Please make sure your device is connected properly via <b>USB</b> cable and try again.\n\n\n\n"
                            "<b>[Troubleshooting]</b>\n"
                            "In terminal enter \"adb devices\" and see if your device is listed there.\n"
                            "Output of \"adb devices\"should looks like this:\n"
                            "$ List of devices attached\n"
                            "$ 003fd0755a4a11ff	<b>device</b>")

            dialog.run()
            print "Please make sure your device is connected properly and try again"
            dialog.destroy()


 ### Screenshot Button clicked
    def toolbutton_screenshot_toggled(self, widget):
        if self.toolbutton_screenshot.get_active() == False:
            self.buttons_state_res()
            self.image_logo.show()
        else:
            self.image_logo.hide()
            self.buttons_state_res()
            self.toolbutton_screenshot.handler_block(self.toolbutton_screenshot_handler_id)
            self.toolbutton_screenshot.set_active(True)
            self.toolbutton_screenshot.handler_unblock(self.toolbutton_screenshot_handler_id)
            self.box_screenshot.show()
            #self.on_button_capture_clicked(self)

 ### Download Button clicked
    def toolbutton_download_toggled(self, widget):
        print "Button Download clicked"
        self.files_count()
        if self.toolbutton_download.get_active() == False:
            self.buttons_state_res()
            self.image_logo.show()
        else:
            self.image_logo.hide()
            self.buttons_state_res()
            self.toolbutton_download.handler_block(self.toolbutton_download_handler_id)
            self.toolbutton_download.set_active(True)
            self.toolbutton_download.handler_unblock(self.toolbutton_download_handler_id)
            self.box_download.show()


 ### Send Button clicked
    def toolbutton_send_toggled(self, widget):
        print "Button Send clicked"
        if self.toolbutton_send.get_active() == False:
            self.buttons_state_res()
            self.image_logo.show()
        else:
            self.image_logo.hide()
            self.buttons_state_res()
            self.toolbutton_send.handler_block(self.toolbutton_send_handler_id)
            self.toolbutton_send.set_active(True)
            self.toolbutton_send.handler_unblock(self.toolbutton_send_handler_id)
            self.box_send.show()

 ### Advanced Button clicked
    def toolbutton_advanced_toggled(self, widget):
        print "Button Advanced clicked"
        if self.toolbutton_advanced.get_active() == False:
            self.buttons_state_res()
            self.image_logo.show()
        else:
            self.image_logo.hide()
            self.buttons_state_res()
            self.toolbutton_advanced.handler_block(self.toolbutton_advanced_handler_id)
            self.toolbutton_advanced.set_active(True)
            self.toolbutton_advanced.handler_unblock(self.toolbutton_advanced_handler_id)
            self.box_advanced.show()


##
##################################### /// END Toolbar buttons END /// ######################################



#### Checking fi dir exists and creating Directory if not ######
    def dir_creator(self, dir_path):
        if os.path.isdir(dir_path):
            #print dir_path + " exists."
            pass
        else:
            os.makedirs(dir_path)
            print dir_path +" directory has been created to store necessary files."


#### Clining system on exit...
    def on_ubuntu_touch_manager_window_destroy(self, widget):
#        os.system("clear")
        print "cleaning temporary files..."
        if os.path.isfile("/tmp/UTM.upload"):
            os.system("rm /tmp/UTM.upload")
            print "/tmp/UTM.upload removed."



