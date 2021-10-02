function check_for_online_slots()
{
    has_online = false
    $(':checkbox').each(function () {
        if(this.checked)
        {
            label = $("label[for='"+$(this).attr("id")+"']").text();
            if (label.includes("Online"))
            {
                has_online = true
                return false;
            }
        }
    })
    if(has_online)
    {
        $('#id_zoom_url').parent().show();
        $('#id_zoom_url').prop('required',true);
    }
    else
    {
        $('#id_zoom_url').parent().hide();
        $('#id_zoom_url').prop('required',false);
    }
}

function setup_zoom_input()
{
    // Initially hide the Zoom field
    $('#id_zoom_url').parent().hide();

    // Show/hide the Zoom field depending on whether
    // online slots are selected.
    $(':checkbox').each(function () {
        $(this).change(function() {
            check_for_online_slots()
        });
    });

}


