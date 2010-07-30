// kate: space-indent on; indent-width 2; replace-tabs on;

Ext.namespace('Ext.ux');

Ext.ux.UserEditorPanel = function( config ){
  Ext.apply( this, config );

  userRecord = Ext.data.Record.create([
    { name: 'id',       type: 'int'    },
    { name: 'name',     type: 'string' },
    { name: 'password', type: 'string' },
    { name: 'owner',    type: 'int'    },
    { name: 'admin',    type: 'bool'   },
    { name: 'delete',   type: 'bool'   }
    ]);

  userAdminStore = new Ext.data.DirectStore({
    baseParams: { server: this.server },
    directFn: Mumble.users,
    fields:   userRecord,
    autoLoad: true,
    remoteSort: false
    });

  adminColumn = new Ext.grid.CheckColumn({
    header:    gettext("Admin on root channel"),
    dataIndex: 'admin',
    width:     50
    });

  deleteColumn = new Ext.grid.CheckColumn({
    header:    gettext("Delete"),
    dataIndex: 'delete',
    width:     50
    });

  ownerCombo = new Ext.form.ComboBox({
    name:           'owner',
    hiddenName:     'owner_id',
    forceSelection: true,
    triggerAction:  'all',
    valueField:     'uid',
    displayField:   'uname',
    store: new Ext.data.DirectStore({
      directFn: Mumble.djangousers,
      fields:   [ 'uid', 'uname' ],
      autoLoad: true
      })
    });

  Ext.applyIf( this, {
    title:  gettext("User List"),
    store:  userAdminStore,
    viewConfig: { forceFit: true },

    cm: new Ext.grid.ColumnModel( [ {
        header:    gettext("name"),
        dataIndex: 'name',
        sortable:  true,
        editor:    new Ext.form.TextField({
          allowBlank: false
          })
      }, {
        header:    gettext("Account owner"),
        dataIndex: 'owner',
        editor:    ownerCombo,
        sortable:  true,
        renderer:  function( value ){
          if( value == '' ) return '';
          items = ownerCombo.store.data.items;
          for( i = 0; i < items.length; i++ )
            if( items[i].data.uid == value )
              return items[i].data.uname;
          }
      }, adminColumn, {
        header:    gettext("Change password"),
        dataIndex: 'password',
        editor: new Ext.form.TextField({
          inputType: 'password'
          }),
        renderer: function( value ){
          ret = '';
          for( i = 0; i < value.length; i++ )
            ret += '*';
          return ret;
          }
      }, deleteColumn ] ),

    tbar:   [{
        text:     gettext("Add"),
        handler : function(){
          userAdminStore.add( new userRecord( {
            id:       -1,
            name:     gettext('New User'),
            admin:    false,
            owner:    '',
            password: '',
            'delete': false
          } ) );
        }
      }, {
      text:     gettext("Save"),
        handler : function(){
          data = [];
          for( i = 0; i < userAdminStore.data.items.length; i++ ){
            rec = userAdminStore.data.items[i];
            if( rec.dirty ){
              data.push(rec.data);
            }
          }
          var conn = new Ext.data.Connection();
          conn.request( {
            url:     userAdminStore.url,
            params:  { data: Ext.encode( data ) },
            success: function(){
              for( i = 0; i < userAdminStore.data.items.length; i++ ){
                rec = userAdminStore.data.items[i];
                if( rec.data['delete'] == true )
                  userAdminStore.remove( rec );
                else if( rec.dirty ){
                  rec.commit();
                }
              }
            }
          });
        }
      }, {
        text:    gettext("Resync with Murmur"),
        handler: function(){
          userAdminStore.reload({
            params: { 'resync': 'true' }
          });
        }
      }],
    plugins: [ adminColumn, deleteColumn ]
  });
  Ext.ux.UserEditorPanel.superclass.constructor.call( this );
};

Ext.extend( Ext.ux.UserEditorPanel, Ext.grid.EditorGridPanel, {
} );

Ext.reg( 'userEditorPanel', Ext.ux.UserEditorPanel );
