// kate: space-indent on; indent-width 4; replace-tabs on;

Ext.namespace('Ext.ux');

Ext.ux.IFrameComponent = Ext.extend(Ext.BoxComponent, {
    // http://www.extjs.com/forum/showthread.php?p=54416#post54416
    onRender : function(ct, position){
        this.el = ct.createChild({tag: 'iframe', id: 'iframe-'+ this.id, frameBorder: 0, src: this.url});
    }
});


Ext.ux.ButtonIframeWindow = function( config ){
    Ext.apply( this, config );

    Ext.apply( this, {
        scope: this,
        enableToggle: true,
        toggleHandler: function(button, state){
            if( !this.wnd ){
                this.wnd = new Ext.Window({
                    title: this.windowTitle || this.text,
                    layout: 'fit',
                    items:  new Ext.ux.IFrameComponent({ url: this.url }),
                    width:  window.viewsize.width  - 200,
                    height: window.viewsize.height - 100,
                    scope: this,
                    buttons: [{
                        text: gettext('Open in new window'),
                        scope: this,
                        handler: function(){
                            window.open( this.url );
                            this.toggle( false );
                        }
                    }],
                    listeners: {
                        beforeclose: function(){
                            this.ownerButton.toggle( false, false );
                            this.ownerButton.wnd = null;
                        }
                    },
                });
                this.wnd.ownerButton = this;
            }
            if( state ){
                this.wnd.show();
                mypos = this.getPosition();
                mysize = this.getSize();
                winsize = this.wnd.getSize();
                this.wnd.setPosition(
                    (window.viewsize.width - winsize.width) / 2,
                    mypos[1] - winsize.height
                    );
            }
            else
                this.wnd.hide();
        }
    });
    Ext.ux.ButtonIframeWindow.superclass.constructor.call( this );
}

Ext.extend( Ext.ux.ButtonIframeWindow, Ext.Button, {
} );

Ext.reg( 'buttonIframeWindow', Ext.ux.ButtonIframeWindow );

