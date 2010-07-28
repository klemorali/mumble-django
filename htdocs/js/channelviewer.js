// kate: space-indent on; indent-width 4; replace-tabs on;

Ext.namespace('Ext.ux');

Ext.ux.MumbleChannelViewer = function( config ){
    Ext.apply( this, config );

    Ext.applyIf( this, {
        title: gettext("Channel Viewer"),
        root: {
            text: gettext("Loading..."),
            leaf: true
        },
        buttons: [{
            text:    gettext("Refresh"),
            handler: this.refresh,
            scope:   this
        }],
    } );

    Ext.ux.MumbleChannelViewer.superclass.constructor.call( this );
    this.refresh();
}

Ext.extend( Ext.ux.MumbleChannelViewer, Ext.tree.TreePanel, {
    refresh: function(){
        var conn = new Ext.data.Connection();
        conn.request({
            url:    this.source_url,
            scope:  this,
            success: function( resp, opt ){
                var respdata = Ext.decode( resp.responseText );
                var root = {
                    text: respdata.name,
                    id:   "mumbroot",
                    leaf: false,
                    icon: '/static/mumble/mumble.16x16.png',
                    children: [],
                };
                function populateNode( node, json ){
                    var subchan_users = 0;
                    for( var i = 0; i < json.channels.length; i++ ){
                        var child = {
                            text: json.channels[i].name,
                            id:   ("channel_" + json.channels[i].id),
                            leaf: true,
                            icon: '/static/mumble/channel.png',
                            children: [],
                        };
                        node.leaf = false;
                        node.children.push( child );
                        subchan_users += populateNode( child, json.channels[i] );
                    }
                    for( var i = 0; i < json.users.length; i++ ){
                        var child = {
                            text: json.users[i].name,
                            id:   ("user_" + json.users[i].id),
                            leaf: true,
                            icon: '/static/mumble/talking_off.png',
                        };
                        node.leaf = false;
                        node.children.push( child );
                    }
                    if( json.id == 0 || json.users.length > 0 || subchan_users )
                        node.expanded = true;
                    return subchan_users + json.users.length;
                }
                populateNode( root, respdata.root );
                this.setRootNode( root );
            },
            failure: function( resp, opt ){
                alert("fail");
            },
        });
    },
} );

Ext.reg( 'mumblechannelviewer', Ext.ux.MumbleChannelViewer );
