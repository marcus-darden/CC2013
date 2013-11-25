function set_openid(openid, provider)
{
    u = openid.search('<username>')
    if (u != -1) {
        // openid requires username
        user = prompt('Enter your ' + provider + ' username:')
        openid = openid.substr(0, u) + user
    }
    $('#openid').val(openid);
}

