gquery = django.jQuery

gquery(document).ready(function(){
	file = document.getElementById('id_photo');
	if (file == null){
		file = gquery('<input type="file" id="id_photo" name="photo">');
		gquery('#user_form').append(file);
	}

	gquery('#id_photo_link').click(function(){
		gquery('#id_photo').click();
		return false;
	});
	gquery('#id_photo').change(function(){
		var input = document.getElementById("id_photo");
		var file = input.files[0];
		if ( window.FileReader ) {  
			var reader = new FileReader();  
			reader.onloadend = function (e) {  
			    	img = document.getElementById('image_view');
				img.src = e.target.result;
			};
			reader.readAsDataURL(file);
		}
	});
});
