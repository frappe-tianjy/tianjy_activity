import frappe
from frappe.core.doctype.version.version import get_diff
from .tianjy_activity.doctype.tianjy_activity.tianjy_activity import TianjyActivity
from .tianjy_activity.doctype.tianjy_activity_configuration.tianjy_activity_configuration import TianjyActivityConfiguration


def to_json(data):
	return frappe.as_json(data, indent=0, separators=(",", ":"))

def get_changed(current, before):
	if not before and (amended_from := current.get("amended_from")):
		before = frappe.get_doc(current.doctype, amended_from)
	if not before:
		return 'Create', []

	diff = get_diff(before, current)
	if not diff: return None, []
	changed = []
	for field, value in diff['added']:
		changed.append(dict(field=field, type="Row Added", new=to_json(value)))
	for field, value in diff['removed']:
		changed.append(dict(field = field, type="Row Removed", old = to_json(value)))
	for field, old, new in diff['changed']:
		changed.append(dict(field = field, type="Changed", old = old, new = new))
	for field, row_name, row_index, row in diff['row_changed']:
		for row_field, old, new in row:
			changed.append(dict(field = field, type="Row Changed", row_name = row_name, row_index = row_index, row_field = row_field, old = old, new = new))

	if len(changed) == 1:
		c = changed[0]
		if c['type'] == 'Changed' and c['field'] == 'docstatus':
			old = c['old']
			new = c['new']
			if old == 0 and new == 1:
				return 'Submit', []
			elif old == 1 and new == 2:
				return 'Cancel', []
			elif old == 2 and new == 0:
				return 'Amend', []
	for c in changed:
		if c['type'] != 'Changed' or c['field'] != 'docstatus': continue;
		old = c['old']
		new = c['new']
		if old != 2 or new != 0: continue
		return 'Amend', changed
	return 'Change', changed


def on_trash(doc, *args, **argv):
	if frappe.flags.in_install or frappe.flags.in_patch: return
	doctype = doc.doctype
	if doctype == TianjyActivity.DOCTYPE: return
	cfg = TianjyActivityConfiguration.find(doctype)
	if not cfg: return
	TianjyActivity.create(doc, 'Delete')


def after_rename(doc, method, old, new, merge, *args, **argv):
	print(old, new, merge)
	if frappe.flags.in_install or frappe.flags.in_patch: return
	doctype = doc.doctype
	if doctype == TianjyActivity.DOCTYPE: return
	cfg = TianjyActivityConfiguration.find(doctype)
	if not cfg: return
	TianjyActivity.create(doc, 'Rename', old_name=old, merge=1 if merge else 0)

def on_change(doc, *args, **argv):
	if frappe.flags.in_install: return
	doctype = doc.doctype
	if doctype == TianjyActivity.DOCTYPE: return
	doc_before = doc.get('_doc_before_save', None)
	if not frappe.db.exists(doctype, doc.name): return
	if not doc_before and frappe.flags.in_patch: return
	cfg = TianjyActivityConfiguration.find(doctype)
	if not cfg: return

	type, changed = get_changed(doc, doc_before)
	if not type: return
	TianjyActivity.create(doc, type, changed=changed)



def comment_on_change(comment, *args, **argv):
	if frappe.flags.in_install: return
	if comment.comment_type != 'Comment': return
	if not frappe.db.exists('Comment', comment.name): return
	doctype = comment.reference_doctype
	comment_before = comment.get('_doc_before_save', None)
	if not comment_before and frappe.flags.in_patch: return
	cfg = TianjyActivityConfiguration.find(doctype)
	if not cfg: return

	type, changed = get_changed(comment, comment_before)
	if not type: return
	type = f'Comment {type}'
	TianjyActivity.create(
		frappe.get_doc(doctype, comment.reference_name),
		type,
		comment=comment.name,
		changed=changed
	)

def comment_on_trash(comment, *args, **argv):
	if frappe.flags.in_install or frappe.flags.in_patch: return
	if comment.comment_type != 'Comment': return
	doctype = comment.reference_doctype
	cfg = TianjyActivityConfiguration.find(doctype)
	if not cfg: return


	doc = frappe.get_doc(doctype, comment.reference_name)
	TianjyActivity.create(doc, 'Comment Delete', old = to_json(comment.as_dict()))
