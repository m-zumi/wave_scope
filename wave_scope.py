#!/usr/bin/env python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------#
# Wave Socpe
#
# Copyright (C) Tetsuya Morizumi
# created: 2011-01-15 
#----------------------------------------------------------------------------#

import math
from gimpfu import *
import pygtk
pygtk.require('2.0')
import pango
import cairo
import gtk

class PixelFetcher:
        def __init__(self, drawable):
            self.col = -1
            self.row = -1
            self.img_width = drawable.width
            self.img_height = drawable.height
            self.img_bpp = drawable.bpp
            self.img_has_alpha = drawable.has_alpha
            self.tile_width = gimp.tile_width()
            self.tile_height = gimp.tile_height()
            self.bg_colour = '\0\0\0\0'
            self.bounds = drawable.mask_bounds
            self.drawable = drawable
            self.tile = None
        def get_pixel(self, x, y):
            sel_x1, sel_y1, sel_x2, sel_y2 = self.bounds

            col = x / self.tile_width
            coloff = x % self.tile_width
            row = y / self.tile_height
            rowoff = y % self.tile_height

            if col != self.col or row != self.row or self.tile == None:
                    self.tile = self.drawable.get_tile(False, row, col)
                    self.col = col
                    self.row = row
            return self.tile[coloff, rowoff]

        def get_pixel_sy(self, x, y):
            rgb = self.get_pixel(x, y)
            # sYCC
            return 0.299 * ord(rgb[0]) + 0.587 * ord(rgb[1]) + 0.114 * ord(rgb[2])
        def get_pixel_y(self, x, y):
            rgb = self.get_pixel(x, y)
            return ord(rgb[0])
        def get_pixel_r(self, x, y):
            pixel = self.get_pixel(x, y)
            return ord(pixel[0])
        def get_pixel_g(self, x, y):
            pixel = self.get_pixel(x, y)
            return ord(pixel[1])
        def get_pixel_b(self, x, y):
            pixel = self.get_pixel(x, y)
            return ord(pixel[2])


class WaveViewer(gtk.DrawingArea):
    def __init__(self, tdrawable):
        gtk.DrawingArea.__init__(self)

        self.__tdrb = tdrawable
        self.__width = 0
        self.__height = 0
        self.dx = 0.0
        self.dy = 0.0
        self.x0 = 0
        self.x1 = 0
        self.y0 = 0
        self.y1 = 0
        self.direction = 0
        self.y_on = False
        self.r_on = True
        self.g_on = True
        self.b_on = True
        self.max_line = 8
        self.connect('size-allocate', self.size_allocate)
        self.connect('expose-event', self.expose_event)
        self.set_flags(gtk.CAN_FOCUS | gtk.HAS_FOCUS)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.connect('button-press-event', self.button_press_event)

    def button_press_event(self, widget, event):
        self.queue_draw()

    def size_allocate(self, widget, allocation):
        # get chenge size
        self.__width = allocation.width
        self.__height = allocation.height

    def expose_event(self, widget, event):
        if self.__tdrb.visible == False:
            gtk.main_quit()

        ctx = widget.window.cairo_create()
        ctx.set_source_rgb(0., 0., 0.)
        ctx.paint()

        pf = PixelFetcher(self.__tdrb)
        (enable, self.x0, self.y0, self.x1, self.y1) = pdb.gimp_drawable_mask_bounds(self.__tdrb)
        if enable == 0:
            return

        width = abs(self.x1 - self.x0)
        height = abs(self.y1 - self.y0)
        if self.direction == 0:
            self.dx = float(self.__width) / float(width - 1)
            self.dy = float(self.__height) / 255.0
        else:
            self.dx = float(self.__width) / 255.0
            self.dy = float(self.__height) / float(height - 1)

        ctx.set_line_width(1)
        self.draw_scale(ctx)

        ctx.set_line_width(2)
        if self.__tdrb.is_rgb == 1:
            if self.y_on :
                ctx.set_source_rgba(0.8, 0.8, 0.8, 0.8)
                self.draw_wave(ctx, pf.get_pixel_sy)
            if self.r_on :
                ctx.set_source_rgba(1, 0, 0, 0.8)
                self.draw_wave(ctx, pf.get_pixel_r)
            if self.g_on :
                ctx.set_source_rgba(0, 1, 0, 0.8)
                self.draw_wave(ctx, pf.get_pixel_g)
            if self.b_on :
                ctx.set_source_rgba(0, 0.8, 1, 0.8)
                self.draw_wave(ctx, pf.get_pixel_b)
        else:
            ctx.set_source_rgb(0.8, 0.8, 0.8)
            self.draw_wave(ctx, pf.get_pixel_y)

    def draw_scale(self, ctx):
        ctx.set_source_rgb(1,0.6,0)
        if self.direction == 0:
            for n in range(1, 8):
                ctx.move_to(0, self.dy * (256/8) * n)
                ctx.rel_line_to(self.__width, 0) 
                ctx.stroke()
        else:
            for n in range(1, 8):
                ctx.move_to(self.dx * (256/8) * n, 0)
                ctx.rel_line_to(0, self.__height) 
                ctx.stroke()

    def draw_wave(self, ctx, pf_get_pixel):
        if self.direction == 0:
            yend = self.y0 + self.max_line
            if self.y1 < yend :
                yend = self.y1
            for y in range(self.y0, yend):
                y_val = pf_get_pixel(self.x0, y)
                ctx.move_to(0, (255.0 - y_val) * self.dy)
                for x in range(self.x0 + 1, self.x1):
                    px = pf_get_pixel(x, y)
                    ctx.rel_line_to(self.dx, (y_val - px) * self.dy)
                    y_val = px
            ctx.stroke()
        else:
            xend = self.x0 + self.max_line
            if self.x1 < xend:
                xend = self.x1
            for x in range(self.x0, xend):
                x_val = pf_get_pixel(x, self.y0)
                ctx.move_to(x_val * self.dx, 0)
                for y in range(self.y0 + 1, self.y1):
                    px = pf_get_pixel(x, y)
                    ctx.rel_line_to((px - x_val) * self.dx, self.dy)
                    x_val = px
            ctx.stroke()

    def set_direction(self, d):
        self.direction = d
        self.queue_draw()
    def set_y(self, on = True):
        self.y_on = on
        self.queue_draw()
    def set_r(self, on = True):
        self.r_on = on
        self.queue_draw()
    def set_g(self, on = True):
        self.g_on = on
        self.queue_draw()
    def set_b(self, on = True):
        self.b_on = on
        self.queue_draw()

class MainWindow:
    def __init__(self, timg, tdrawable):
        self.window = gtk.Window()
        self.window.set_title('Wave Scope')
        self.window.connect('destroy_event', self.destory)
        self.window.connect('delete_event', self.destory)
        self.window.set_default_size(256, 256)

        wv = WaveViewer(tdrawable)

        cmbbox = gtk.combo_box_new_text()
        cmbbox.append_text('Horizontal')
        cmbbox.append_text('Vertical')
        cmbbox.set_active(0)
        cmbbox.connect('changed', self.set_direction, wv.set_direction)

        chkbox_y = gtk.CheckButton('Y(sYCC)')
        chkbox_y.set_active(False)
        chkbox_y.connect('toggled', self.sel_show_color, wv.set_y)
        chkbox_r = gtk.CheckButton('R')
        chkbox_r.set_active(True)
        chkbox_r.connect('toggled', self.sel_show_color, wv.set_r)
        chkbox_g = gtk.CheckButton('G')
        chkbox_g.set_active(True)
        chkbox_g.connect('toggled', self.sel_show_color, wv.set_g)
        chkbox_b = gtk.CheckButton('B')
        chkbox_b.set_active(True)
        chkbox_b.connect('toggled', self.sel_show_color, wv.set_b)

        hbox_chkbox = gtk.HBox(False, 10)

        hbox_chkbox.add(cmbbox)
        hbox_chkbox.add(chkbox_y)
        hbox_chkbox.add(chkbox_r)
        hbox_chkbox.add(chkbox_g)
        hbox_chkbox.add(chkbox_b)

        halign = gtk.Alignment(0, 0, 0, 0)
        halign.add(hbox_chkbox)

        vbox = gtk.VBox(False, 1)
        vbox.add(wv)
        vbox.pack_start(halign, False, False, 3)

        self.window.add(vbox)

        self.window.show_all()

    def set_direction(self, combobox, set_dir):
        set_dir(combobox.get_active())

    def sel_show_color(self, widget, toggle_color):
        toggle_color(widget.get_active())

    def destory(self, widget, data=None):
        gtk.main_quit()
        return False


def wave_scope(timg, tdrawable):
    mw = MainWindow(timg, tdrawable)
    gtk.main()

register(
        "python_fu_WaveScope",
        "Wave Scope",       # blurb
        "Wave Scope",       # help
        "Tetsuya Morizumi", # author
        "Tetsuya Morizumi", # copyright
        "2011-01-21",       # date
        "<Image>/Colors/WaveScope",
        "RGB*, GRAY*",
        [],
        [],
        wave_scope)

main()

