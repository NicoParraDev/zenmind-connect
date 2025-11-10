function iniciarMap(){
  var coord = {lat:-33.4472824 ,lng: -70.6575998};
  var map = new google.maps.Map(document.getElementById('map'),{
    zoom: 10,
    center: coord
  });
  var marker = new google.maps.Marker({
    position: coord,
    map: map
  });
}