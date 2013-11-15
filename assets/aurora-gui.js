
/* Javascript functions for Aurora control pages 
J. Foote 2013, with welcome additions from Suraj Sharma. */


//var finalHex, CURRENT_COLOR;

/* accepts parameters
 * h  Object = {h:x, s:y, v:z}
 * OR 
 * h, s, v
 */
/*
function HSVtoRGB(h, s, v) {
    var r, g, b, i, f, p, q, t;
    if (h && s === undefined && v === undefined) {
        s = h.s, v = h.v, h = h.h;
    }
    i = Math.floor(h * 6);
    f = h * 6 - i;
    p = v * (1 - s);
    q = v * (1 - f * s);
    t = v * (1 - (1 - f) * s);
    switch (i % 6) {
    case 0: r = v, g = t, b = p; break;
    case 1: r = q, g = v, b = p; break;
    case 2: r = p, g = v, b = t; break;
    case 3: r = p, g = q, b = v; break;
    case 4: r = t, g = p, b = v; break;
    case 5: r = v, g = p, b = q; break;
    }
    return {
        r: Math.floor(r * 255),
        g: Math.floor(g * 255),
        b: Math.floor(b * 255)
    };
}

function hexFromRGB(r, g, b) { 
    var hex = [
	r.toString( 16 ),
	g.toString( 16 ),
	b.toString( 16 )
    ];
    $.each( hex, function( nr, val ) {
	if ( val.length === 1 ) {
            hex[ nr ] = "0" + val;
	}
    });
    return hex.join( "" ).toUpperCase();
}
*/
//function refreshSwatchHue() {
    //var hue = $( "#hue" ).slider( "value" );
    //var color  = HSVtoRGB(hue/255.0, 1.0, 0.9);
    //finalHex = hexFromRGB(color.r,color.g,color.b);
    //$("#color-hash").html(finalHex);
    //$( "#swatch" ).css( "background-color", "#" + finalHex ); 
    //$( "#hue" ).css('background', "#" + finalHex ); 
    //$( "#hue .ui-slider-range" ).css('background', "#" + finalHex ); 
//}

//function refreshSwatch() {
//    var red = $( "#red" ).slider( "value" ),
//    green = $( "#green" ).slider( "value" ),
//    blue = $( "#blue" ).slider( "value" );
//    finalHex = hexFromRGB( red, green, blue );
//    $("#color-hash").html(finalHex);
//    $( "#swatch" ).css( "background-color", "#" + finalHex );
//}
 
  function ajax_request(data){
      $.ajax({
	  url: "./sparkle.html",
	  type: "POST",
	  dataType: "json",
	  data: data,
	  success: ajax_success,
	  error: ajax_fail,
	  context: document.body
      });

  }

function ajax_success(data, text_status, response){
    console.log('success',data);
    console.log('success',data[0].response);
    console.log('success',data[0].response[1]);
	console.log(data[0].response[0]);
    //window.alert(data[0].response[0]);
}

function ajax_fail(response, text_status, code){
    console.log('ajax fail');
    //window.alert(data[0]);
}


function log(msg) {
    setTimeout(function() {
	throw new Error(msg);
    }, 0);
}  

function submit_request(){
    var params = {};
    params["function"] = "sparkle";
    params["speed"] = $( "#speed" ).slider( "option", "value" );
    params["random"] = $( "#random" ).slider( "option", "value" );

    params["p1"] = $( "#inp1" ).val();
    params["foo"] = "bar";
    //params["colors"] =finalHex; // will now contain Hex code for selected color like FF0000 for Red, 00FF00 for Green and 0000FF for Blue.
	params["colors"] = $('#color').val().slice(1);
    ajax_request(params)
}

function submit_button(the_button, the_action){
    var params = {};
    params["function"] = the_button;

	if (the_action == "generative") {
    	params["smooth"] = $( "#smooth-generative" ).slider( "option", "value" );
	} else if (the_action == "pattern"){
    	params["smooth"] = $( "#smooth-pattern" ).slider( "option", "value" );
	}
    ajax_request(params)

}

//function submit_test(){
//    var params = {};
//    params["function"] = "test";
    //params["speed"] = $( "#speed" ).slider( "option", "value" );
//    params["p1"] = $( "#inp1" ).val();
//    params["p2"] = $( "#inp2" ).val();
//    params["p3"] = $( "#inp3" ).val();
//    params["foo"] = "bar";
//    params["colors"] =finalHex; // will now contain Hex code for selected color like FF0000 for Red, 00FF00 for Green and 0000FF for Blue.
//    ajax_request(params)
//}

//$(function() {
    
    //$( "#red, #green, #blue" ).slider({
	//orientation: "horizontal",
	//range: "min",
	//max: 255,
	//value: 127,
	//slide: refreshSwatch,
	//change: refreshSwatch
    //});

//});

$(function() {
    $('#speed').slider({ value: 51 });
    $('#random').slider({ value: 51 });
    $('#smooth-generative').slider({ value: 51 });
    $('#smooth-pattern').slider({ value: 51 });
    $('#speed, #random','#smooth-generative', '#smooth-pattern').draggable();

//$('#red, #green, #blue, #speed').draggable();
  //  $( "#red" ).slider( "value", 255 );
    //$( "#green" ).slider( "value", 140 );
    //$( "#blue" ).slider( "value", 60 );

    //$( "#hue" ).slider({
	//orientation: "horizontal",
	//range: "min",
	//max: 255,
	//value: 127,
	//slide: refreshSwatchHue,
	//change: refreshSwatchHue
    //});
    
    //$( "#hue" ).draggable();
    //$( "#hue" ).slider({ value: 127 });


	//init tabs
	$('.nav-tabs a').click(function (e) {
	  e.preventDefault()
	  $(this).tab('show')
	});
	
	//init color picker
	//$('#colorpicker').farbtastic(function(value){ 
	//	CURRENT_COLOR = value;
	//});
	$('#colorpicker').farbtastic('#color');
	
	$('#controls-form').submit(function(e) {
		e.preventDefault();
		e.stopPropagation();
	
		submit_request();
	});
	

	//init patterns
    $('.actions button').click(function(e) {
		e.preventDefault();
		var thisButtonValue = $(this).data('value'); 
		var thisButtonAction = $(this).data('action'); 

		//window.alert(thisButtonValue)
		submit_button(thisButtonValue, thisButtonAction);
    });

	//mobile safari stuff - <= iOS 6
	window.addEventListener("load",function() {
	    // Set a timeout...
	    setTimeout(function(){
	        // Hide the address bar!
	        window.scrollTo(0, 1);
	    }, 0);
	});

	

});

