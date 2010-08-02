function renderserverinfos( server ){
    var buf = [];
    if( server.connecturl ){
        buf.push( String.format( '{0}: <a href="{1}">{1}</a>', gettext("Server Address"), server.connecturl ) );
    }
    if( server.url ){
        buf.push( String.format( '{0}: {1}', gettext("Website"), server.url ) );
    }
    buf.push( interpolate( "This server is running Murmur version %s.", [server.prettyversion] ) );
    buf.push( interpolate(
        ngettext( "Currently, %s user is registered.", "Currently, %s users are registered.", server.users_regged ),
        [server.users_regged] ) );
    buf.push( interpolate(
        ngettext( "Currently, %s user is online.", "Currently, %s users are online.", server.users_online ),
        [server.users_online] ) );
    buf.push( interpolate(
        ngettext( "Currently, there is %s channel.", "Currently, there are %s channels.", server.channel_cnt ),
        [server.channel_cnt] ) );
    if( server.uptime ){
        buf.push( interpolate( "This server is running since %s.", [server.upsince] ) );
    }
    buf.push( String.format( '<a href="{0}">{1}</a>', server.minurl, gettext( "Switch to minimal view" ) ) );

    res = ['<div class="mumble-ext" id="serverstuffz">', '<ul>'];
    for( var i = 0; i < buf.length; i++ )
        res.push( '<li>'+buf[i]+'</li>' );
    res.push( '</ul><br /><br />' );
    res.push( String.format( '<b>{0}:</b><br />', gettext("Welcome message") ) );
    res.push( String.format( '<div style="padding: 10px">{0}</div>', server.motd ) );
    res.push( '</div>' );
    return res.join('');
}
