// kate: space-indent on; indent-width 4; replace-tabs on;

Ext.namespace('Ext.ux');

Ext.ux.MumbleChannelViewer = function( config ){
    Ext.apply( this, config );

    Ext.applyIf( this, {
        title: "Channel View",
        root: {
            text: "ohai",
            leaf: true
        }
    } );

    var conn = new Ext.data.Connection();
    conn.request({
        url:    this.source_url,
        scope:  this,
        success: function( resp, opt ){
            respdata = Ext.decode( resp.responseText );
            root = {
                text: respdata.name,
                id:   "mumbroot",
                leaf: false,
                icon: '/static/mumble/mumble.16x16.png',
                children: [],
            };
            function populateNode( node, json ){
                subchan_users = 0;
                for( var i = 0; i < json.channels.length; i++ ){
                    child = {
                        text: json.channels[i].name,
                        id:   ("channel_" + json.channels[i].id),
                        leaf: false,
                        icon: '/static/mumble/channel.png',
                        children: [],
                    };
                    node.children.push( child );
                    subchan_users += populateNode( child, json.channels[i] );
                }
                for( var i = 0; i < json.users.length; i++ ){
                    child = {
                        text: json.users[i].name,
                        id:   ("user_" + json.users[i].id),
                        leaf: true,
                        icon: '/static/mumble/talking_off.png',
                    };
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

    Ext.ux.MumbleChannelViewer.superclass.constructor.call( this );
}

Ext.extend( Ext.ux.MumbleChannelViewer, Ext.tree.TreePanel, {
    
} );

Ext.reg( 'mumblechannelviewer', Ext.ux.MumbleChannelViewer );

function render_mumble( divname, data_url ){
    var mainpanel = new Ext.Panel({
        renderTo: divname,
        height:   600,
        layout:   "border",
        items: [{
            xtype: "mumblechannelviewer",
            region: "west",
            width: 350,
            split: true,
            source_url: data_url,
        }, {
            xtype: "tabpanel",
            region: "center",
            activeTab: 0,
            items: [{
                title: "fail",
                html: "fail",
            }, {
                title: "omg",
                html: "omg"
            }],
        }],
    });
}
