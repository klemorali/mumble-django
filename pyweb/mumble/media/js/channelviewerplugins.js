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

            tabitems = [{
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
                    xtype: "form",
                    border: false,
                    items: [{
                        xtype: "checkbox",
                        fieldLabel: gettext("Authenticated"),
                        disabled: true,
                        name:  "a",
                        checked: (this.userdata.userid != -1)
                    }, {
                        xtype: "checkbox",
                        fieldLabel: gettext("Self-Deafened"),
                        disabled: true,
                        name:  "sd",
                        checked: this.userdata.selfDeaf
                    }, {
                        xtype: "checkbox",
                        fieldLabel: gettext("Deafened"),
                        disabled: true,
                        name:  "d",
                        checked: this.userdata.deaf
                    }, {
                        xtype: "checkbox",
                        fieldLabel: gettext("Self-Muted"),
                        disabled: true,
                        name:  "sm",
                        checked: this.userdata.selfMute
                    }, {
                        xtype: "checkbox",
                        fieldLabel: gettext("Muted"),
                        disabled: true,
                        name:  "m",
                        checked: this.userdata.mute
                    }, {
                        xtype: "checkbox",
                        fieldLabel: gettext("Suppressed"),
                        disabled: true,
                        name:  "s",
                        checked: this.userdata.suppress
                    }, {
                        xtype: "checkbox",
                        fieldLabel: gettext("Priority Speaker"),
                        disabled: true,
                        name:  "p",
                        checked: this.userdata.prioritySpeaker
                    }, {
                        xtype: "checkbox",
                        fieldLabel: gettext("Recording"),
                        disabled: true,
                        name:  "r",
                        checked: this.userdata.recording
                    }]
                }];
            if( this.is_admin ){
                tabitems.push({
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
                }, {
                    xtype: "form",
                    border: false,
                    title: gettext("Send message"),
                    defaults: { "anchor": "-20px" },
                    items: [{
                        xtype: "htmleditor",
                        fieldLabel: 'x',
                        hideLabel: true,
                        name: "message"
                    }],
                    fbar: [{
                        scope: this,
                        text: gettext("Send message"),
                        handler: function(btn){
                            f = btn.ownerCt.ownerCt.getForm().getValues();
                            Mumble.sendMessage(this.serverid, this.userdata.session, f.message);
                        }
                    }]
                });
            }

            this.wnd = new Ext.Window({
                title: this.windowTitle || gettext("User details"),
                layout: 'fit',
                items: {
                    xtype: "tabpanel",
                    activeTab: 0,
                    border: false,
                    items: tabitems,
                },
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
            this.chandata = chandata;

            tabitems = [{
                xtype: "form",
                border: false,
                title: gettext("Channel description"),
                defaults: { "anchor": "-20px" },
                items: [{
                    xtype: "textfield",
                    fieldLabel: "x",
                    hideLabel: true,
                    name:  "name",
                    value: chandata.name
                }, {
                    xtype: "htmleditor",
                    fieldLabel: 'x',
                    hideLabel: true,
                    name: "description",
                    value: chandata.description
                }],
            }];
            if( this.is_admin ){
                Ext.apply( tabitems[0], {
                    fbar: [{
                        text: gettext('Add subchannel...'),
                        scope: this,
                        handler: function(btn){
                            Ext.Msg.prompt(gettext('Name'), gettext('Please enter the channel name:'), function(btn, text){
                                if (btn == 'ok'){
                                    Mumble.addChannel( this.serverid, text, this.chandata.id );
                                }
                            }, this);
                        }
                    }, {
                        scope: this,
                        text: gettext("Submit name/description"),
                        handler: function(btn){
                            f = btn.ownerCt.ownerCt.getForm().getValues();
                            Mumble.renameChannel(this.serverid, this.chandata.id, f.name, f.description);
                        }
                    }, {
                        text: gettext('Delete channel'),
                        scope: this,
                        handler: function(btn){
                            Ext.Msg.confirm(
                                gettext('Confirm channel deletion'),
                                interpolate(gettext('Are you sure you want to delete channel %s?'), [this.chandata.name]),
                                function(btn){
                                    if( btn == 'yes' ){
                                        Mumble.removeChannel( this.serverid, this.chandata.id );
                                    }
                                }, this);
                        }
                    }]
                });
                tabitems.push({
                    xtype: "form",
                    border: false,
                    title: gettext("Send message"),
                    defaults: { "anchor": "-20px" },
                    items: [{
                        xtype: "checkbox",
                        fieldLabel: gettext('Cascade to subchannels'),
                        name: 'tree'
                    }, {
                        xtype: "htmleditor",
                        fieldLabel: 'x',
                        hideLabel: true,
                        name: "message"
                    }],
                    fbar: [{
                        scope: this,
                        text: gettext("Send message"),
                        handler: function(btn){
                            f = btn.ownerCt.ownerCt.getForm().getValues();
                            Mumble.sendMessageChannel(this.serverid, this.chandata.id, (f.tree || false), f.message);
                        }
                    }]
                });
            }

            this.wnd = new Ext.Window({
                title: this.windowTitle || gettext("Channel details"),
                layout: 'fit',
                items: [{
                    xtype: "tabpanel",
                    activeTab: 0,
                    items: tabitems
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
