// kate: space-indent on; indent-width 4; replace-tabs on;

Ext.namespace('Ext.ux');

Ext.ux.ButtonLogout = Ext.extend(Ext.Button, {
    text: gettext('Logout'),
    handler: function(){
        Accounts.logout( function(provider, response){
                if( response.result.success ){
                    window.location.reload();
                }
                else{
                    Ext.Msg.show({
                        title: gettext("Login error"),
                        msg:   gettext("Unable to log out."),
                        icon:  Ext.MessageBox.ERROR,
                        buttons: Ext.MessageBox.OK
                        });
                }
            } );
    }
});

function handleLogin(){
    Accounts.login(Ext.fly('login_field_username').getValue(), Ext.fly('login_field_password').getValue(),
        function(provider, response){
            if( response.result.success ){
                window.location.reload();
            }
            else{
                Ext.Msg.show({
                    title: gettext("Login error"),
                    msg:   gettext("Unable to log in."),
                    icon:  Ext.MessageBox.ERROR,
                    buttons: Ext.MessageBox.OK
                    });
            }
        });
}

Ext.ux.ButtonLogin = Ext.extend(Ext.Button, {
    text: gettext('Login'),
    enableToggle: true,
    toggleHandler: function(button, state){
        if( !this.wnd ){
            this.wnd = new Ext.Window({
                title: gettext('Login'),
                closable: false,
                width:  300,
                height: 130,
                layout: 'fit',
                items: {
                    id: 'login_form',
                    layout: 'form',
                    border: false,
                    defaults: { anchor: '-20px' },
                    buttons: [{
                        text: gettext('Submit'),
                        handler: handleLogin
                    }],
                    items: [{
                        id: 'login_field_username',
                        xtype: "textfield",
                        width: 50,
                        fieldLabel: gettext("User name"),
                        name: "username",
                        listeners: {
                            specialkey: function( f, e ){
                                if( e.getKey() == e.ENTER )
                                    Ext.fly('login_field_password').focus();
                            }
                        }
                    }, {
                        id: 'login_field_password',
                        xtype: 'textfield',
                        fieldLabel: gettext("Password"),
                        inputType: "password",
                        name: "password",
                        listeners: {
                            specialkey: function( f, e ){
                                if( e.getKey() == e.ENTER )
                                    handleLogin();
                            }
                        }
                    }],
                },
            });
        }
        if( state ){
            this.wnd.show();
            mypos = this.getPosition();
            mysize = this.getSize();
            winsize = this.wnd.getSize();
            this.wnd.setPosition(
                mypos[0] + mysize.width - winsize.width,
                mypos[1] - winsize.height
                );
            (function(){
                Ext.fly('login_field_username').focus();
            }).defer(250);
        }
        else
            this.wnd.hide();
    }
});
