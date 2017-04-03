/**
 * Created by Wondimagegn Tesfaye Beshah on 4/1/2017.
 */
function apply_anchor() {
    tags = ['h1', 'h2', 'h3', 'h4', 'h5'];

    for (var i = 0; i < tags.length; i++) {

        headings = document.getElementsByTagName(tags[i]);

        for (var j = 0; j < headings.length; j++){
            inner_text = headings[j].innerHTML;
            anchor = inner_text.replace(/ /g, '_').replace('-', '_').
            toLowerCase();

            headings[j].insertAdjacentHTML(
            'afterbegin',
            '<a href="#'+anchor+'" id="'+anchor+'"></a>'
            );
        }

    }

}
apply_anchor();


