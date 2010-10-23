// kate: space-indent on; indent-width 4; replace-tabs on;

Ext.namespace('Ext.ux');

Ext.ux.BanViewerPanel = function( config ){
    Ext.apply( this, config );

    Ext.applyIf( this, {
        xtype: 'grid',
        title: gettext('Bans'),
        colModel: new Ext.grid.ColumnModel([{
                header: gettext('Timestamp'),
                dataIndex: 'start',
                width: 100,
                renderer: function( value ){
                    return new Date(value*1000).format( "Y-m-d H:i:s" );
                }
            }, {
                header: gettext('Duration'),
                width: 100,
                dataIndex: 'duration'
            }, {
                header: gettext('Reason'),
                width: 500,
                dataIndex: 'reason'
            }]),
        bbar: [{
            iconCls: 'x-tbar-loading',
            tooltip: gettext('Refresh'),
            handler: function(){
                this.ownerCt.ownerCt.store.reload();
            }
        }],
        store: new Ext.data.DirectStore({
            baseParams: {'server': this.server},
            directFn: Mumble.bans,
            paramOrder: ['server'],
            root: 'data',
            fields: ['start', 'address', 'bits', 'duration', 'reason'],
            autoLoad: true,
            remoteSort: false
            }),
        viewConfig: { forceFit: true }
    });
    Ext.ux.LogViewerPanel.superclass.constructor.call( this );
}

Ext.extend( Ext.ux.BanViewerPanel, Ext.grid.EditorGridPanel, {
} );

Ext.reg( 'banViewerPanel', Ext.ux.BanViewerPanel );

