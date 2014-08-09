$('.download a').on('click', function(event) {
    $(this).parents('tr').addClass('downloaded');
    var tpb_id = $(this).data('id');
    $.get('/download/' + tpb_id);
});