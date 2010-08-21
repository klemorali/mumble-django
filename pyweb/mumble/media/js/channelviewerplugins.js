// kate: space-indent on; indent-width 4; replace-tabs on;

Ext.namespace('Ext.ux');

Ext.ux.MumbleUserEditor = Ext.extend( Ext.Component, {
    clickHandler: function( node, ev ){
        if( typeof node.attributes.userdata != "undefined" ){
            this.activate(node.attributes.userdata);
        }
    },

    init: function( tree ){
        this.tree = tree;
        tree.on("click", this.clickHandler, this);
    },

    activate: function( userdata ){
        if( !this.wnd ){
            this.userdata = userdata;
            this.wnd = new Ext.Window({
                title: this.windowTitle || gettext("User details"),
                layout: 'fit',
                items: [{
                    xtype: "tabpanel",
                    activeTab: 0,
                    border: false,
                    items: [{
                        xtype: "form",
                        border: false,
                        title: gettext("User comment"),
                        items: [{
                            xtype: "htmleditor",
                            fieldLabel: 'x',
                            hideLabel: true,
                            name: "comment",
                            value: userdata.comment,
                        }],
                    }, {
                        title: gettext("Avatar"),
                        scope: this,
                        listeners: {
                            afterrender: function( panel ){
                                Mumble.hasTexture( this.scope.serverid, this.scope.userdata.userid, function(provider, response){
                                    if( response.result.has ){
                                        panel.el.dom.children[0].children[0].innerHTML = String.format(
                                            '<img src="{0}" alt="avatar" />', response.result.url
                                            );
                                    }
                                    else{
                                        panel.el.dom.children[0].children[0].innerHTML =
                                            gettext("This user does not have an Avatar.");
                                    }
                                } );
                            }
                        },
                        html:  gettext("Loading..."),
                    }, {
                        title: gettext("Infos"),
                        html:  "<ul><li>admin: yes</li><li>registered: maybe</li></ul>",
                    }, {
                        xtype: "form",
                        border: false,
                        title: gettext("Administration"),
                        items: [{
                            xtype: "checkbox",
                            fieldLabel: gettext("Ban"),
                            name: "ban"
                        }, {
                            xtype: "numberfield",
                            fieldLabel: gettext("Ban duration"),
                            value: 3600,
                            name: "duration"
                        }, {
                            xtype: "label",
                            text:  gettext("Only if banning. Set to 0 for permanent ban, any other value for the ban duration in seconds."),
                            cls:   "form_hint_label",
                        }, {
                            xtype: "textfield",
                            fieldLabel: gettext("Reason"),
                            name:  "reason"
                        }],
                        fbar: [{
                            scope: this,
                            text: gettext("Kick"),
                            handler: function(btn){
                                f = btn.ownerCt.ownerCt.getForm().getValues();
                                Mumble.kickUser(
                                    this.serverid, this.userdata.session, f.reason, (f.ban || false), parseInt(f.duration)
                                    );
                            }
                        }, {
                            text: gettext("Mute"),
                            enableToggle: true,
                            scope: this,
                            ref:   '../mutebutton',
                            pressed: this.userdata.mute,
                            disabled: this.userdata.deaf,
                            toggleHandler: function(btn, state){
                                Mumble.muteUser(this.serverid, this.userdata.session, state);
                            }
                        }, {
                            text: gettext("Deafen"),
                            enableToggle: true,
                            scope: this,
                            ref:   '../deafenbutton',
                            pressed: this.userdata.deaf,
                            toggleHandler: function(btn, state){
                                Mumble.deafenUser(this.serverid, this.userdata.session, state);
                                if( state )
                                    btn.refOwner.mutebutton.toggle(true, true);
                                btn.refOwner.mutebutton.setDisabled(state);
                            }
                        }],
                    }],
                }],
                width:  500,
                height: 300,
                scope: this,
                listeners: {
                    beforeclose: function(){
                        this.owner.wnd = null;
                    }
                },
            });
            this.wnd.owner = this;
        }
        if( !this.wnd.isVisible() ){
            this.wnd.show();
            mypos = this.tree.getPosition();
            mysize = this.tree.getSize();
            this.wnd.setPosition( mypos[0] + mysize.width - 50, mypos[1] + 50 );
        }
        else{
            this.wnd.close();
        }
    },
} );

Ext.ux.MumbleChannelEditor = Ext.extend( Ext.Component, {
    clickHandler: function( node, ev ){
        if( typeof node.attributes.chandata != "undefined" ){
            this.activate(node.attributes.chandata);
        }
    },

    init: function( tree ){
        this.tree = tree;
        tree.on("click", this.clickHandler, this);
    },

    activate: function( chandata ){
        if( !this.wnd ){
            this.wnd = new Ext.Window({
                title: this.windowTitle || gettext("Channel details"),
                layout: 'fit',
                items: [{
                    xtype: "tabpanel",
                    activeTab: 0,
                    items: [{
                        xtype: "form",
                        border: false,
                        title: gettext("Channel description"),
                        defaults: { "anchor": "-20px" },
                        items: [{
                            xtype: "htmleditor",
                            fieldLabel: 'x',
                            hideLabel: true,
                            name: "description",
                            value: chandata.description,
                        }],
                    }],
                }],
                width:  500,
                height: 300,
                scope: this,
                listeners: {
                    beforeclose: function(){
                        this.owner.wnd = null;
                    }
                },
            });
            this.wnd.owner = this;
        }
        if( !this.wnd.isVisible() ){
            this.wnd.show();
            mypos = this.tree.getPosition();
            mysize = this.tree.getSize();
            this.wnd.setPosition( mypos[0] + mysize.width - 50, mypos[1] + 50 );
        }
        else{
            this.wnd.close();
        }
    },
} );
