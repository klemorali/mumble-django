// kate: space-indent on; indent-width 4; replace-tabs on;

Ext.namespace('Ext.ux');

Ext.ux.LogViewerPanel = function( config ){
    Ext.apply( this, config );

    Ext.applyIf( this, {
        xtype: 'grid',
        title: gettext('Log messages'),
        colModel: new Ext.grid.ColumnModel([{
                header: gettext('Timestamp'),
                dataIndex: 'timestamp',
                width: 100,
                renderer: function( value ){
                    return new Date(value*1000).format( "Y-m-d H:i:s" );
                }
            }, {
                header: gettext('Log entry'),
                width: 500,
                dataIndex: 'txt'
            }]),
        bbar: [{
            text: gettext('Filter') + ':'
        }, {
            xtype: 'textfield',
            name: 'filter',
            listeners: {
                render: function(c) {
                    Ext.QuickTips.register({
                        target: c.getEl(),
                        text:   gettext('Enter a string to filter the logs by and press Enter. To display all log entries, empty this field.')
                    });
                },
                specialkey: function( field, ev ){
                    if( ev.getKey() == ev.ENTER ){
                        field.ownerCt.ownerCt.store.baseParams.filter = field.getValue();
                        field.ownerCt.ownerCt.store.reload();
                    }
                }
            }
        }, '-', {
            iconCls: 'x-tbar-loading',
            tooltip: gettext('Refresh'),
            handler: function(){
                this.ownerCt.ownerCt.store.reload();
            }
        }],
        store: new Ext.data.DirectStore({
            baseParams: {'server': this.server, 'start': 0, 'limit': 100, 'filter': ''},
            directFn: Mumble.log,
            paramOrder: ['server', 'start', 'limit', 'filter'],
            root: 'data',
            fields: ['timestamp', 'txt'],
            autoLoad: true,
            remoteSort: false
            }),
        viewConfig: { forceFit: true }
    });
    Ext.ux.LogViewerPanel.superclass.constructor.call( this );
}

Ext.extend( Ext.ux.LogViewerPanel, Ext.grid.EditorGridPanel, {
} );

Ext.reg( 'logViewerPanel', Ext.ux.LogViewerPanel );

