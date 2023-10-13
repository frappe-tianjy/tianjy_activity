// Copyright (c) 2023, guigu and contributors
// For license information, please see license.txt

/**
 *
 * @param {HTMLElement} parent
 * @param {string} doctype
 * @param {string} name
 */
function setLink(parent, doctype, name) {
	const a = document.createElement('a');
	let f;
	// eslint-disable-next-line no-cond-assign
	while (f = parent.firstChild) {
		a.appendChild(f);
	}
	parent.appendChild(a);
	a.href = frappe.utils.get_form_link(doctype, name);

}
frappe.ui.form.on('Tianjy Activity', {
	refresh: function(frm) {
		const dt = frm.doc.doc_type;
		const dn = frm.doc.doc;
		if (dt && dn) {
			setLink(frm.fields_dict.doc.disp_area, dt, dn);
		}
		const {comment} = frm.doc;
		if (comment) {
			setLink(frm.fields_dict.comment.disp_area, 'Comment', comment);
		}
	},
});
