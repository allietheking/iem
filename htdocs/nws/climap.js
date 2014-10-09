var renderattr = "high";
var vectorLayer;
var map;
var element;

function updateMap(){
	renderattr = $('#renderattr').val();
	vectorLayer.setStyle( vectorLayer.getStyle() );
}

function updateDate(){
	var fullDate = $.datepicker.formatDate("yy-mm-dd", 
										$("#datepicker").datepicker('getDate'));
	map.removeLayer(vectorLayer);
	vectorLayer = makeVectorLayer(fullDate);
	map.addLayer(vectorLayer);
	
}

function makeVectorLayer(dt){
	return new ol.layer.Vector({
		source: new ol.source.GeoJSON({
		  	projection: ol.proj.get('EPSG:4326'),
		    url: '/geojson/cli.py?dt='+dt
	  	}),
	  	style: function(feature, resolution){
	  		style = [new ol.style.Style({
	  	        fill: new ol.style.Fill({
	  	          color: 'rgba(255, 255, 255, 0.6)'
	  	        }),
	  	        stroke: new ol.style.Stroke({
	  	          color: '#319FD3',
	  	          width: 1
	  	        }),
	  	        text: new ol.style.Text({
	  	          font: '12px Calibri,sans-serif',
	  	          text: feature.get(renderattr),
	  	          fill: new ol.style.Fill({
	  	            color: '#000'
	  	          }),
	  	          stroke: new ol.style.Stroke({
	  	            color: '#fff',
	  	            width: 3
	  	          })
	  	        })
	  	      })];
	  		return style;
	  	}
	});
}

$(document).ready(function(){


	$( "#datepicker" ).datepicker({
		dateFormat:"DD, d MM, yy",
		minDate: new Date(2009, 1, 1),
		maxDate: new Date()
	});
	$("#datepicker").datepicker('setDate', new Date());
    $("#datepicker").change(function(){
        updateDate();
     });

vectorLayer = makeVectorLayer($.datepicker.formatDate("yy-mm-dd",new Date()));

map = new ol.Map({
        target: 'map',
        layers: [
                 new ol.layer.Tile({
                     title: "Global Imagery",
                     source: new ol.source.TileWMS({
                       url: 'http://maps.opengeo.org/geowebcache/service/wms',
                       params: {LAYERS: 'bluemarble', VERSION: '1.1.1'}
                     })
                 }),
          vectorLayer
        ],
        view: new ol.View({
            projection: 'EPSG:4326',
            center: [-95, 42],
            zoom: 3,
            maxResolution: 0.703125
          })
      });

element = document.getElementById('popup');

var popup = new ol.Overlay({
	  element: element,
	  positioning: 'bottom-center',
	  stopEvent: false
	});
map.addOverlay(popup);
	
$(element).popover({
    'placement': 'top',
    'html': true,
    content: function() { return $('#popover-content').html(); }
  });

// display popup on click
map.on('click', function(evt) {
  var feature = map.forEachFeatureAtPixel(evt.pixel,
      function(feature, layer) {
        return feature;
      });
  if (feature) {
    var geometry = feature.getGeometry();
    var coord = geometry.getCoordinates();
    popup.setPosition(coord);
    var content = "<p><strong>"+ feature.get('name') 
    	+"<br />High: "+ feature.get('high') +" Norm:"+ feature.get("high_normal") +" Rec:"+ feature.get("high_record")
    	+"<br />Low: "+ feature.get('low') +" Norm:"+ feature.get("low_normal") +" Rec:"+ feature.get("low_record")
    	+"<br />Precip: "+ feature.get('precip') +" Rec:"+ feature.get("precip_record")
    	+"<br />Snow: "+ feature.get('snow') +" Rec:"+ feature.get("snow_record")
    	+"</p>";
    $('#popover-content').html(content);
    $(element).popover('show');
    
    $('#clireport').html("<h3>Loading text, one moment please...</h3>");
    $.get(feature.get('link'), function(data) {
        $('#clireport').html("<pre>"+ data +"</pre>");
     });
    
  } else {
    $(element).popover('hide');
  }

});

});