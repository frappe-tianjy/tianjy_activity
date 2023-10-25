def select(value, df, doc):
	from frappe import _
	return _(value)

def dynamic_link(value, df, doc):
	try:
		import frappe
		dt = doc.get(df.options)
		if not dt: return
		return frappe.get_doc(dt, value).get_title()
	except:
		...


def link(value, df, doc):
	try:
		import frappe
		return frappe.get_doc(df.options, value).get_title()
	except:
		...
