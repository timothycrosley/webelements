'''
    Containers.py

    Elements that combine several base elements to enable containing elements in pop-up menus,
    tabs, or other complex layouts

    Copyright (C) 2015  Timothy Edmund Crosley

    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 2
    of the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
'''

from . import DOM, Base, Buttons, ClientSide, Display, Factory, HiddenInputs, Inputs, Layout
from .Factory import Composite
from .MethodUtils import CallBack
from .MultiplePythonSupport import *

Factory = Factory.Factory("Containers")


class DropDownMenu(Layout.Box):
    """
        Defines a dropdown menu webelement -- where clicking a button exposes or hides a menu.
    """
    __slots__ = ('toggle', 'menu', 'openOnly', 'parentElement')
    properties = Layout.Box.properties.copy()
    properties['openOnly'] = {'action':'classAttribute', 'type':'bool'}
    properties['parentElement'] = {'action':'classAttribute'}


    def _create(self, id=None, name=None, parent=None, **kwargs):
        Layout.Box._create(self, id  and (id + "Container") or "", name, parent)
        self.toggle = None
        self.menu = None
        self.openOnly = False
        self.parentElement = None

    def setToggleButton(self, toggleButton, relation="thedom.peer"):
        """
            Sets the button that controls the toggling of the menu

            toggleButton - the control button
            relation - the relational javascript method to call to get the menu aka "thedom.peer" or
                      "thedom.childElement"
        """
        self.toggle = toggleButton
        if self.id:
            self.toggle.id = self.id + "-Toggle"

        self.toggle.addJavascriptEvent('onclick',
                                       "thedom.clickDropDown(%s(this, 'WMenu'), %s, this, %s);" %
                                        (relation, ((self.openOnly and "true") or "false"),
                                    (self.parentElement and "thedom.get('%s')" % self.parentElement) or "null"))
        self.toggle.addClass("WToggle")
        return toggleButton

    def add(self, childElement, ensureUnique=True):
        """
            Overrides the behavior of adding a child element, by making the first element the menu toggle
            and the second the menu contents.
        """
        if not self.toggle:
            return self.setToggleButton(Layout.Box.add(self, childElement, ensureUnique))
        elif not self.menu:
            self.menu = Layout.Box.add(self, childElement, ensureUnique)
            if self.id:
                self.menu.id = self.id + ":Content"
            self.menu.addClass("WMenu")
            self.menu.addJavascriptEvent('onclick', 'thedom.State.isPopupOpen = true;')
            self.menu.hide()
            return self.menu
        else:
            return Layout.Box.add(self, childElement)

Factory.addProduct(DropDownMenu)


class Help(DropDownMenu):
    """
        Shows help info or text
    """
    __slots__ = ('label', )
    properties = DropDownMenu.properties.copy()
    properties['text'] = {'action':'label.setText'}

    def _create(self, id=None, name=None, parent=None, **kwargs):
        DropDownMenu._create(self, id, name, parent, **kwargs)
        self.add(Display.Image(src="images/help.png")).addClass("Clickable")
        layout = self.add(Layout.Vertical())
        self.label = layout.add(Display.Label)
        self.addsTo = layout


Factory.addProduct(Help)


class CollapsedText(DropDownMenu):
    """
        Shows a limited amount of text revealing the rest when the user hovers over
    """
    __slots__ = ('lengthLimit', '__text', 'label', 'completeText')
    properties = DropDownMenu.properties.copy()
    properties['lengthLimit'] = {'action':'classAttribute', 'type':'int'}
    properties['text'] = {'action':'setText'}

    def _create(self, id=None, name=None, parent=None, **kwargs):
        DropDownMenu._create(self, id, name, parent, **kwargs)

        self.lengthLimit = 40
        self.label = self.add(Display.Label)
        self.__text = ''

    def setText(self, text):
        """
            Sets the collapse able text
        """
        self.__text = text

    def _render(self):
        DropDownMenu._render(self)

        text = self.text()
        if len(text) > int(self.lengthLimit or 0):
            self.label.parent.addJavascriptEvent('onmouseover',
                                               "thedom.displayDropDown(thedom.peer(this, 'WMenu'));")
            self.label.parent.addJavascriptEvent('onmouseout', "thedom.hide(thedom.peer(this, 'WMenu'));")
            self.label.setText(text[:int(self.lengthLimit) - 3] + "...")
            self.completeText = self.add(Display.Label())
            self.completeText.setText(text)
            self.completeText.style['width'] = 240
        else:
            self.label.setText(text)

    def text(self):
        """
            Returns the set text
        """
        return self.__text

Factory.addProduct(CollapsedText)

class Autocomplete(Layout.Box):
    """
        A text box that opens a drop down menu upon editing
    """
    __slots__ = ('blockTab', 'menu', 'userInput')
    properties = Layout.Box.properties.copy()
    properties['blockTab'] = {'action':'classAttribute', 'type':'bool'}

    def _create(self, id, name=None, parent=None, **kwargs):
        Layout.Box._create(self, id + "Container", name, parent)

        self.blockTab = True
        self.menu = None
        self.userInput = None

        self.add(Inputs.TextBox(id))
        self.userInput.attributes['autocomplete'] = "off"
        self.userInput.addJavascriptEvent('onkeydown', CallBack(self, "jsShowIfActive"))
        self.userInput.addJavascriptEvent('onkeyup', CallBack(self, "jsShowIfActive"))
        self.userInput.addClass("WToggle")

        self.addScript("""if(!document.hasMenuClose){
                            document.hasMenuClose = true;
                            var AutoCompletePopup = null;
                            var MenuClicked = false;
                            var prevFunction = document.onclick;
                            document.onclick =
                            function CloseLastAutocompletePopup()
                            {
                                if(AutoCompletePopup && !MenuClicked){
                                    thedom.hide(AutoCompletePopup)
                                }
                                if(prevFunction)prevFunction();
                                MenuClicked = false;
                            }
                          };""")

    def add(self, childElement, ensureUnique=True):
        """
            Overrides the behavior of add making the first child element the user input
            that will be provided auto complete support, and the second the menu contents which will contain
            the auto complete results on key-up.
        """
        if not self.userInput:
            self.userInput = Layout.Box.add(self, childElement, ensureUnique)
            return self.userInput
        if not self.menu:
            self.menu = Layout.Box.add(self, childElement, ensureUnique)
            self.menu.id = self.id + ":Content"
            self.menu.addClass("WMenu")
            self.menu.hide()
            return self.menu
        else:
            return Layout.Box.add(self, childElement, ensureUnique)

    def jsShowIfActive(self):
        """
            Returns the javascript code necessary to show the drop down menu on key up if there is text present.
        """
        return """if(event.keyCode != ENTER){
                    var menu = thedom.peer(this, 'WMenu');
                    if(this.value""" + (self.blockTab and " && event.keyCode != TAB)" or ")") + """
                    {
                        thedom.show(menu);
                        AutoCompletePopup = menu;
                    }
                    else
                    {
                        thedom.hide(menu);
                        AutoCompletePopup = null;
                    }
                  }
                  """

Factory.addProduct(Autocomplete)


class Tab(Layout.Box):
    """
        A single tab - holds a single element(The tabs content) and the tabs label
    """
    __slots__ = ('tabLabel', 'imageName', 'isSelected')
    signals = Layout.Box.signals + ['selected', 'unselected']
    properties = Layout.Box.properties.copy()
    properties['select'] = {'action':'call', 'type':'bool'}
    properties['text'] = {'action':'tabLabel.setText'}
    properties['imageName'] = {'action':'classAttribute'}
    Base.addChildProperties(properties, Display.Label, 'tabLabel')
    
    class ClientSide(Layout.Box.ClientSide):
        
        def select(self):
            return ClientSide.selectTab(self)

    class TabLabel(Display.Label):
        """
            The label used to represent the tab in the tab-bar
        """
        __slots__ = ()
        tagName = "span"

        def _create(self, id, name=None, parent=None, **kwargs):
            Display.Label._create(self, id=id, name=name, parent=parent)
            self.addClass("WTabLabel")

        def select(self):
            """
                changes the class to reflect a selected tab label
            """
            self.addClass('WSelected')

        def unselect(self):
            """
                changes the class to reflect an unselected tab label
            """
            self.removeClass('WSelected')

    def _create(self, id, name=None, parent=None, **kwargs):
        Layout.Box._create(self, id=id, name=name, parent=parent)

        self.tabLabel = self.TabLabel(id=self.id + "Label", parent=self)
        self.imageName = None
        self.isSelected = False

    def text(self):
        """
            Returns the text associated with this tab.
        """
        return self.tabLabel.text()

    def setText(self, text):
        """
            Sets the display text associated with this tab.
        """
        return self.tabLabel.setText(text)

    def remove(self):
        self.tabLabel.remove()
        return Layout.Box.remove(self)

    def _render(self):
        Layout.Box._render(self)

        if self.imageName:
            image = self.tabLabel.add(Layout.Box())
            image.addClass(self.imageName)
            image.style['margin'] = "auto"
            image.style['clear'] = "both"

    def select(self):
        """
            Displays the tab, and highlights the tab label
        """
        self.isSelected = True
        self.tabLabel.select()
        self.addClass("WSelected")
        self.emit('selected')

    def unselect(self):
        """
            Unhighlights the tab label, and hides the tab
        """
        self.isSelected = False
        self.tabLabel.unselect()
        self.removeClass("WSelected")
        self.emit('unselected')

Factory.addProduct(Tab)
TabLabel = Tab.TabLabel


class TabContainer(Base.Node):
    """
        TabContaier makes it easy to show association between several elements on a page via tabs
    """
    __slots__ = ('tabs', 'selectedTab', 'layout', '__tabLabelContainer__', '__tabContentContainer__')
    __layoutElement__ = Layout.Vertical
    __tabLayoutElement__ = Layout.Horizontal

    def _create(self, id, name=None, parent=None, **kwargs):
        Base.Node._create(self, id, name, parent, **kwargs)

        self.tabs = {}
        self.selectedTab = None

        self.layout = self.add(self.__layoutElement__(id, name, parent))
        self.layout.addClass("W" + self.__class__.__name__)

        self.__tabLabelContainer__ = self.layout.add(self.__tabLayoutElement__())
        self.__tabLabelContainer__.addClass('WTabLabels')
        self.__tabContentContainer__ = self.layout.add(Layout.Box())
        self.__tabContentContainer__.addClass('WTabContents')

    def selectTab(self, tabName):
        """
            Selects an individual tab based upon its name
        """
        tab = self.tabs[tabName]
        if tab == self.selectedTab:
            return
        elif self.selectedTab:
            self.selectedTab.unselect()

        self.selectedTab = tab
        tab.select()

    def add(self, element, ensureUnique=True):
        """
            Overrides the add behavior to make the first add element the tab.
        """
        if isinstance(element, Tab):
            element.tabLabel.addJavascriptEvent('onclick', element.clientSide.select())
            self.tabs[element.id] = element
            element.tabLabel.id = element.id + "Label"
            element.connect('selected', None, self, 'selectTab', element.id)
            if not self.selectedTab or element.isSelected:
                element.select()

            self.__tabLabelContainer__.add(element.tabLabel)
            element.addClass("WTab")
            return self.__tabContentContainer__.add(element)
        else:
            return Base.Node.add(self, element, ensureUnique)

Factory.addProduct(TabContainer)


class VerticalTabContainer(TabContainer):
    """
        Defines a tab container that lays out tabs vertically instead of the default horizontal behavior.
    """
    __layoutElement__ = Layout.Horizontal
    __tabLayoutElement__ = Layout.Vertical

Factory.addProduct(VerticalTabContainer)


class Accordion(Layout.Vertical):
    """
        Defines an accordion, a labeled section of the page, that upon clicking the label has its visibility
        toggled
    """
    __slots__ = ('toggle', 'toggleImage', 'toggleLabel', 'isOpen', 'contentElement', '_scriptAdded')
    properties = Layout.Box.properties.copy()
    properties['open'] = {'action':'call', 'type':'bool'}
    properties['label'] = {'action':'setLabel'}

    class ClientSide(Layout.Vertical.ClientSide):

        def toggle(self):
            element = self.serverSide
            return ClientSide.toggleAccordion(element.contentElement, element.toggleImage, element.isOpen)

        def open(self):
            element = self.serverSide
            return ClientSide.openAccordion(element.contentElement, element.toggleImage, element.isOpen)

        def close(self):
            element = self.serverSide
            return ClientSide.closeAccordion(element.contentElement, element.toggleImage, element.isOpen)

    def _create(self, id, name=None, parent=None, **kwargs):
        Layout.Vertical._create(self, id, name, parent, **kwargs)
        self.addClass("WAccordion")

        self.toggle = self.add(Layout.Box())
        self.toggle.addClass('WAccordionToggle')
        self.toggleImage = self.toggle.add(Display.Image((id or "") + "Image"))
        self.toggleImage.addClass('WLeft')
        self.toggleLabel = self.toggle.add(Display.FreeText())
        self.isOpen = self.toggle.add(HiddenInputs.HiddenBooleanValue(id + "Value"))
        self.contentElement = self.add(Layout.Box(id + "Content"))
        self.contentElement.addClass('WContent')
        self.addsTo = self.contentElement

        self.isOpen.connect('valueChanged', True, self, 'open')
        self.isOpen.connect('valueChanged', False, self, 'close')
        self.close()
        self._scriptAdded = False

    def _render(self):
        if not self._scriptAdded:
            self.toggle.addJavascriptEvent('onclick', self.ClientSide(self).toggle())
            self._scriptAdded = True

    def setLabel(self, text):
        """
            Sets the toggle label text
        """
        self.toggleLabel.setText(text)

    def label(self):
        """
            Returns the toggle label's text
        """
        return self.toggleLabel.text()

    def open(self):
        """
            Makes the accordions content visible
        """
        self.toggleImage.setProperty('src', 'images/hide.gif')
        self.contentElement.show()
        self.isOpen.setValue(True)

    def close(self):
        """
            Hides the accordions content
        """
        self.toggleImage.setProperty('src', 'images/show.gif')
        self.contentElement.hide()
        self.isOpen.setValue(False)


Factory.addProduct(Accordion)


class FormContainer(DOM.Form):
    """
        Defines a form container web element - a portion of the page that contains fields to be submitted back to
        the server.
    """
    __slots__ = ()

    def _create(self, id=None, name=None, parent=None, **kwargs):
        DOM.Form._create(self, id, name, parent, **kwargs)
        self.setProperty('method', 'POST')

    def validators(self, useFullId=True):
        """
            Returns a list of all validators associated with this element and all child elements:   -
                useFullId - if set to True the validators are set against the prefix + id   -
        """
        validatorDict = {}
        validator = getattr(self, 'validator', None)
        if self.editable() and validator:
            validatorDict['chained_validators'] = validator

        for child in self.childElements:
            validatorDict.update(child.validators(useFullId))

        return validatorDict

Factory.addProduct(FormContainer)


class ActionBox(Layout.Vertical):
    """
        Defines a list of actions grouped together under a header
    """
    __slots__ = ('header', 'actions')
    properties = Layout.Vertical.properties.copy()
    properties['header'] = {'action':'header.setText'}

    def _create(self, id=None, name=None, parent=None, **kwargs):
        Layout.Vertical._create(self, id, name, parent, **kwargs)
        self.addClass("WActionBox")

        self.header = self.add(Display.Label())
        self.header.addClass("WActionBoxHeader")

        self.actions = self.add(Display.List())

    def add(self, childElement, ensureUnique=True):
        """
            Overrides the add behavior to see any links passed in as actions.
        """
        if type(childElement) == Buttons.Link:
            return self.actions.add(childElement)
        else:
            return Layout.Vertical.add(self, childElement, ensureUnique=ensureUnique)

Factory.addProduct(ActionBox)


class PageControlPlacement(Layout.Box):
    """
        Defines where on a page a PageControl should be placed, so that a third party library
        (such as DynamicForm) can automatically find and replace the control object with a concrete instance.

        Note: A unique (per-template not page) id is necessary for the automatic replacement to work,
              and an accessor must not be present.
    """
    __slots__ = ('control')
    properties = Layout.Box.properties.copy()
    properties['control'] = {'action':'classAttribute', 'info':'The id of the control to replace this with, '
                                                               'control path is relative and dots are allowed '
                                                               'to access child controls. Use .. to access parent '
                                                               'controls as with python parent imports. '
                                                               'If not specified id is assumed to be the control '
                                                               'name.'}

    def _create(self, id=None, name=None, parent=None, **kwargs):
        Layout.Box._create(self, id, name, parent, **kwargs)
        self.control = id

    def _render(self):
        layout = self.add(Layout.Horizontal(style='height: 50px; padding:10px;',
                                                        **{'class':'WLoading'}))
        layout += Display.Image(src="images/throbber.gif")
        if self.control.lower().endswith('s'):
            layout += Display.Label(text=self.control + " go here...")
        else:
            layout += Display.Label(text=self.control + " goes here...")

Factory.addProduct(PageControlPlacement)
