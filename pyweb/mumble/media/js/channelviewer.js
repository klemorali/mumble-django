// kate: space-indent on; indent-width 4; replace-tabs on;

Ext.namespace('Ext.ux');

if( typeof gettext == "undefined" ){
    // Cope with Django's jsi18n not being available by adding dummy gettext
    gettext = function( text ){
        return text;
    };
    gettext_noop = gettext;
}

Ext.ux.MumbleChannelNodeUI = Ext.extend(Ext.tree.TreeNodeUI, {
    renderElements : function(n, a, targetNode, bulkRender){
        Ext.ux.MumbleUserNodeUI.superclass.renderElements.call( this, n, a, targetNode, bulkRender );
        Ext.DomHelper.applyStyles( this.elNode, 'position: relative' );
        var tpl = new Ext.DomHelper.createTemplate(
            '<img style="position: absolute; top: 0px; right: {pos}px;" src="{imageurl}/{icon}.png"/>'
            );
        var icons = []
        if( a.chandata.description != "" ) icons.push( "comment_seen" );
        var pos = 8;
        for( var i = 0; i < icons.length; i++ ){
            tpl.append( this.elNode, {'imageurl': a.imageurl, 'icon': icons[i], 'pos': pos} );
            pos += 18
        }
    }
});

Ext.ux.MumbleUserNodeUI = Ext.extend(Ext.tree.TreeNodeUI, {
    renderElements : function(n, a, targetNode, bulkRender){
        Ext.ux.MumbleUserNodeUI.superclass.renderElements.call( this, n, a, targetNode, bulkRender );
        Ext.DomHelper.applyStyles( this.elNode, 'position: relative' );
        var tpl = new Ext.DomHelper.createTemplate(
            '<img style="position: absolute; top: 0px; right: {pos}px;" src="{imageurl}/{icon}.png"/>'
            );
        var icons = []
        if( a.userdata.userid != -1 )    icons.push( "authenticated" );
        if( a.userdata.selfDeaf )        icons.push( "deafened_self" );
        if( a.userdata.deaf )            icons.push( "deafened_server" );
        if( a.userdata.selfMute )        icons.push( "muted_self" );
        if( a.userdata.suppress )        icons.push( "muted_suppressed" );
        if( a.userdata.mute )            icons.push( "muted_server" );
        if( a.userdata.comment != "" )   icons.push( "comment_seen" );
        if( a.userdata.prioritySpeaker ) icons.push( "priority_speaker" );
        var pos = 8;
        for( var i = 0; i < icons.length; i++ ){
            tpl.append( this.elNode, {'imageurl': a.imageurl, 'icon': icons[i], 'pos': pos} );
            pos += 18
        }
    }
});

function cmp_channels( left, rite ){
    // Compare two channels, first by position, and if that equals, by name.
    if( typeof left.position != "undefined" && typeof rite.position != "undefined" ){
        byorder = left.position - rite.position;
        if( byorder != 0 )
            return byorder;
    }
    return left.name.localeCompare(rite.name);
}

function cmp_names( left, rite ){
    return left.name.localeCompare(rite.name);
}

Ext.ux.MumbleChannelViewer = function( config ){
    Ext.apply( this, config );

    Ext.applyIf( this, {
        title: gettext("Channel Viewer"),
        refreshInterval: 30000,
        idleInterval: 2,
        autoScroll: true,
        enableDD:   false, // Users need to enable this explicitly
        root: {
            text: gettext("Loading..."),
            leaf: true
        },
        listeners: {}
    });

    Ext.applyIf( this.listeners, {
        dragdrop: function( tree, node, targetdd, ev ){
            if( typeof node.attributes.userdata != "undefined" )
                tree.fireEvent("moveUser", tree, node.attributes.userdata, targetdd.dragOverData.target.attributes.chandata);
            else if( typeof node.attributes.chandata != "undefined" )
                tree.fireEvent("moveChannel", tree, node.attributes.chandata, targetdd.dragOverData.target.attributes.chandata);
        }
    });

    Ext.applyIf( this, {
        // This stuff needs the above applied already
        bbar: [ gettext("Auto-Refresh")+':', {
                xtype:   "checkbox",
                ref:     "../cbAutoRefresh",
                scope:   this,
                handler: this.setAutoRefresh,
                checked: (this.refreshInterval > 0),
            }, {
                xtype:   "numberfield",
                width:   30,
                value:   this.refreshInterval / 1000,
                ref:     "../nfAutoRefreshInterval",
                scope: this,
                selectOnFocus: true,
                listeners: {
                    render: function(c) {
                        Ext.QuickTips.register({
                            target: c.getEl(),
                            text:   gettext('Enter the interval in seconds in which the channel viewer should refresh and hit Enter.')
                        });
                    },
                    specialkey: function( field, ev ){
                        if( ev.getKey() == ev.ENTER ){
                            this.scope.setAutoRefresh(); // lawl
                            this.blur();
                        }
                    }
                },
            }, gettext("Seconds"), '->', {
                xtype:   "button",
                text:    gettext("Refresh"),
                handler: this.refresh,
                scope:   this
            }]
    } );

    Ext.ux.MumbleChannelViewer.superclass.constructor.call( this );

    this.addEvents({
        'moveUser':    true,
        'moveChannel': true
    });

    this.autoRefreshId = 0;
    this.setAutoRefresh();
}

Ext.extend( Ext.ux.MumbleChannelViewer, Ext.tree.TreePanel, {
    setAutoRefresh: function(){
        if( this.autoRefreshId != 0 ){
            clearTimeout( this.autoRefreshId );
        }
        if( this.cbAutoRefresh.getValue() ){
            this.refreshInterval = this.nfAutoRefreshInterval.getValue() * 1000;
            this.autoRefresh();
        }
        else{
            this.refreshInterval = 0;
        }
    },

    autoRefresh: function(){
        this.refresh();
        if( this.refreshInterval > 0 ){
            this.autoRefreshId = this.autoRefresh.defer( this.refreshInterval, this );
        }
    },

    refresh: function(){
        var conn = new Ext.data.Connection();
        conn.request({
            url:    this.source_url,
            scope:  this,
            success: function( resp, opt ){
                var respdata = Ext.decode( resp.responseText );
                var root = {
                    text: respdata.name,
                    nodeType: 'async',
                    id:   "mumbroot",
                    leaf: false,
                    icon: this.imageurl+'/mumble.16x16.png',
                    children: [],
                    chandata: respdata.root,
                    imageurl: this.imageurl
                };
                tree = this;
                function populateNode( node, json ){
                    var subchan_users = 0;
                    json.channels.sort(cmp_channels);
                    for( var i = 0; i < json.channels.length; i++ ){
                        var child = {
                            text: json.channels[i].name,
                            id:   ("channel_" + json.channels[i].id),
                            nodeType: 'async',
                            allowDrag: true,
                            allowDrop: true,
                            draggable: true,
                            icon: tree.imageurl+'/channel.png',
                            children: [],
                            uiProvider: Ext.ux.MumbleChannelNodeUI,
                            chandata: json.channels[i],
                            imageurl: tree.imageurl
                        };
                        node.children.push( child );
                        subchan_users += populateNode( child, json.channels[i] );
                    }
                    json.users.sort(cmp_names);
                    for( var i = 0; i < json.users.length; i++ ){
                        var child = {
                            text: json.users[i].name,
                            id:   ("user_" + json.users[i].session),
                            nodeType: 'async',
                            leaf: true,
                            allowDrag: true,
                            draggable: true,
                            uiProvider: Ext.ux.MumbleUserNodeUI,
                            userdata: json.users[i],
                            imageurl: tree.imageurl
                        };
                        if( json.users[i].idlesecs <= this.idleInterval )
                            child.icon = tree.imageurl+'/talking_on.png';
                        else
                            child.icon = tree.imageurl+'/talking_off.png';
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
                if( this.refreshInterval > 0 )
                    this.cbAutoRefresh.setValue(false);
                Ext.Msg.show({
                    title: gettext("Update error"),
                    msg:   gettext("Querying the server failed, so the channel viewer has not been updated."),
                    icon:  Ext.MessageBox.ERROR,
                    buttons: Ext.MessageBox.OK
                    });
            },
        });
    },
} );

Ext.reg( 'mumblechannelviewer', Ext.ux.MumbleChannelViewer );
