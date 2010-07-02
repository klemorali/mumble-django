// kate: space-indent on; indent-width 4; replace-tabs on;

function render_mumble( divname, urls ){
    var mainpanel = new Ext.Panel({
        renderTo: divname,
        height:   600,
        layout:   "border",
        items: [{
            xtype: "mumblechannelviewer",
            region: "west",
            width: 350,
            split: true,
            source_url: urls.data,
        }, {
            xtype: "tabpanel",
            region: "center",
            activeTab: 0,
            items: [{
                title: gettext("Registration"),
                xtype: "form",
                items: [{
                    name:       "username",
                    fieldLabel: gettext("User name"),
                    xtype:      "textfield",
                }, {
                    name:       "password",
                    fieldLabel: gettext("Password"),
                    xtype:      "textfield",
                    inputType:  "password",
                }],
            }, {
                title: gettext("Administration"),
                xtype: "form",
                items: [{
                    name:       "test",
                    fieldLabel: "testing",
                    xtype:      "textfield",
                }],
            }, {
                title: gettext("User texture"),
                layout: "border",
                items: [{
                    region: "north",
                    layout: "hbox",
                    height: 220,
                    items: [{
                        flex: 1,
                        height: 200,
                        title: gettext("Texture"),
                        html: String.format('<img src="{0}" alt="Avatar" />', urls.myavatar),
                    }, {
                        flex: 1,
                        height: 200,
                        title: gettext("Gravatar"),
                        html: String.format('<img src="{0}" alt="grAvatar" />', urls.gravatar),
                    }],
                }, {
                    region: "center",
                    xtype: "form",
                    items: [{
                        name:       "usegravatar",
                        fieldLabel: gettext("Use Gravatar"),
                        xtype:      "checkbox",
                    }, {
                        name:       "uploadpic",
                        fieldLabel: gettext("Upload Avatar"),
                        xtype:      "textfield",
                        inputType:  "file",
                    }],
                }],
            }, {
                xtype: "userEditorPanel",
                django_users_url: urls.django_users,
                mumble_users_url: urls.mumble_users,
            } ],
        }],
    });
}
