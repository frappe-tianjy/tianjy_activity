import frappe
from frappe import _
from frappe.core.doctype.version.version import get_diff
from .tianjy_activity.doctype.tianjy_activity.tianjy_activity import TianjyActivity
from .tianjy_activity.doctype.tianjy_activity_configuration.tianjy_activity_configuration import TianjyActivityConfiguration


def to_json(data):
	return frappe.as_json(data, indent=0, separators=(",", ":"))

def get_type_to_text(fieldtype: str):
	types = frappe.get_hooks('tianjy_types')
	if not isinstance(types, dict): return
	type = types.get(fieldtype, None)
	if not isinstance(type, dict): return
	fn = type.get('to_text')
	if not fn: return
	if isinstance(fn, list): fn = fn[0]
	if not fn or not isinstance(fn, str): return
	fn = frappe.get_attr(fn)
	if not callable(fn): return
	return fn


def get_changed(current, before):
	if not before and (amended_from := current.get("amended_from")):
		before = frappe.get_doc(current.doctype, amended_from)
	if not before:
		return 'Create', []


	meta = frappe.get_meta(current.doctype)

	def get_field(field, meta):
		fields = meta.get('fields', {'fieldname': field})
		if not fields: return
		df = fields[0]
		return df
	def get_label(df):
		label = df.label
		return  f"{_(label)}({df.fieldname})" if label else df.fieldname


	diff = get_diff(before, current)
	if not diff: return None, []
	changed = []
	for field, value in diff['added']:
		data = dict(field=field, type="Row Added", new=to_json(value))
		if df := get_field(field, meta):
			data['field'] = get_label(df)
		changed.append(data)
	for field, value in diff['removed']:
		data = dict(field = field, type="Row Removed", old = to_json(value))
		if df := get_field(field, meta):
			data['field'] = get_label(df)
		changed.append(data)
	for field, old, new in diff['changed']:
		data = dict(field = field, type="Changed", old = old, new = new, old_value = old, new_value = new)
		if df := get_field(field, meta):
			data['field'] = get_label(df)
			if (new != None or old != None) and (fn := get_type_to_text(df.fieldtype)):
				if new != None and (value := fn(new, df, current)):
					data['new_value'] = value
				if old != None and (value := fn(old, df, before)):
					data['old_value'] = value
		changed.append(data)
	for field, row_name, row_index, row in diff['row_changed']:
		for row_field, old, new in row:
			data = dict(field = field, type="Row Changed", row_name = row_name, row_index = row_index, row_field = row_field, old = old, new = new, old_value = old, new_value = new)
			if df := get_field(row_field, meta):
				data['field'] = get_label(df)
				if df.fieldtype not in ['Table', 'Table Multiple']: return data
				table_meta = frappe.get_meta(df.options)
				if tdf := get_field(row_field, table_meta):
					data['row_field'] = get_label(tdf)
					if (new != None or old != None) and (fn := get_type_to_text(tdf.fieldtype)):
						if new != None and (value := fn(new, tdf, current.get(field, {}))):
							data['new_value'] = value
						if old != None and (value := fn(old, tdf, before.get(field, {}))):
							data['old_value'] = value
			changed.append(data)

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
	try:
		doc_before = doc._doc_before_save
	except:
		return
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
	TianjyActivity.create(doc, 'Comment Delete', comment=comment.name, old = to_json(comment.as_dict()))


def file_after_insert(file, *args, **argv):
	if frappe.flags.in_install: return
	doctype = file.attached_to_doctype
	if frappe.flags.in_patch: return
	cfg = TianjyActivityConfiguration.find(doctype)
	if not cfg: return

	try:
		doc = frappe.get_doc(doctype, file.attached_to_name)
		TianjyActivity.create(doc, 'File Add', file=file.file_url)
	except:
		...

def file_on_trash(file, *args, **argv):
	if frappe.flags.in_install or frappe.flags.in_patch: return
	doctype = file.attached_to_doctype
	cfg = TianjyActivityConfiguration.find(doctype)
	if not cfg: return


	try:
		doc = frappe.get_doc(doctype, file.attached_to_name)
		TianjyActivity.create(doc, 'File Remove', file=file.file_url)
	except:
		...
