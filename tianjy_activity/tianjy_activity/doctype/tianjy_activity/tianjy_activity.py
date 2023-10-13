# Copyright (c) 2023, guigu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class TianjyActivity(Document):
	DOCTYPE="Tianjy Activity"
	@classmethod
	def create(cls, doc: Document, type: str, **p):
		activity = frappe.new_doc(cls.DOCTYPE)
		activity.set('doc_type', doc.doctype)
		activity.set('doc', doc.name)
		activity.set('type', type)
		activity.set('title',  doc.get_title())
		from tianjy_organization import get_doc_organization
		if organization := get_doc_organization(doc):
			activity.set('organization', organization)
		for k,v in p.items():
			activity.set(k, v)
		activity.insert(ignore_permissions = True, ignore_links = True)
