gquery = django.jQuery
gquery(document).ready(function(){
		gquery('li.tab a').click(function(){
gquery('li.tab a').each(function(index, el){
gquery(el).removeClass('active');
});
gquery(this).addClass('active');
		gquery('.event_content').each(function(index, el){
			gquery(el).hide();
		});
		gquery(this.rel).show();
		return false;
	})
})
