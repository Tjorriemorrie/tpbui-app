$('.download a').on('click', function(event) {
    setDownload($(this).data('id'));
});

function setDownload(tpb_id) {
    console.info(tpb_id);
    $('table').find('[data-id=' + tpb_id + ']').parents('tr').addClass('downloaded');
    $.get('/download/' + tpb_id);
}