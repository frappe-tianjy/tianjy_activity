// Copyright (c) 2023, guigu and contributors
// For license information, please see license.txt

/**
 *
 * @param {HTMLElement} parent
 * @param {string} href
 * @param {string} name
 */
function setLink(parent, href) {
	const a = document.createElement('a');
	let f;
	// eslint-disable-next-line no-cond-assign
	while (f = parent.firstChild) {
		a.appendChild(f);
	}
	parent.appendChild(a);
	a.href = href;

}
frappe.ui.form.on('Tianjy Activity', {
	refresh: function(frm) {
		const dt = frm.doc.doc_type;
		const dn = frm.doc.doc;
		if (dt && dn) {
			const href = frappe.utils.get_form_link(dt, dn);
			setLink(frm.fields_dict.doc.disp_area, href);
		}
		const {comment, file} = frm.doc;
		if (comment) {
			const href = frappe.utils.get_form_link('Comment', comment);
			setLink(frm.fields_dict.comment.disp_area, href);
		}
		if (file) {
			setLink(frm.fields_dict.file.disp_area, file);
		}
	},
});
