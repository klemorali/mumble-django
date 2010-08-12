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
                        html: userdata.comment || gettext("No user comment set"),
                        title: gettext("User comment"),
                    }, {
                        title: gettext("Avatar"),
                        html:  '<img src="http://www.gravatar.com/avatar/6a11052bfa1ae52aa63fc0001417158d.jpg?d=monsterid&s=80" />',
                    }, {
                        title: gettext("Infos"),
                        html:  "<ul><li>admin: yes</li><li>registered: maybe</li></ul>",
                    }, {
                        xtype: "form",
                        border: false,
                        title: gettext("Kick/Ban"),
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
                        html: chandata.description || gettext("No channel description set"),
                        title: gettext("Channel description"),
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
