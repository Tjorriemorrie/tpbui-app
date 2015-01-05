$('.download a').on('click', function(event) {
    setDownload($(this).data('key'));
    return true;
});

function setDownload(key) {
    console.info(key);
    $('table').find('[data-key=' + key + ']').parents('tr').addClass('downloaded');
    $.get('/download/' + key);
}