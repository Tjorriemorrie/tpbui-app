$('.download a').on('click', function(event) {
    setDownload($(this).data('key'), $(this).data('magnet'));
});

function setDownload(key, magnet) {
//    console.info('key', key);
//    console.info('magnet', magnet);
    $('table').find('[data-key=' + key + ']').parents('tr').toggleClass('downloaded');
    var res = $.get('/download/' + key);
    res.error(function(res) {
        alert('Could not save your download!');
    });
    res.always(function() {
        window.location.href = magnet;
    });
}