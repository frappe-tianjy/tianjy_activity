# Copyright (c) 2023, guigu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class TianjyActivityConfiguration(Document):
	DOCTYPE="Tianjy Activity Configuration"
	@classmethod
	def find(cls, dt: str):
		try:
			return frappe.get_last_doc(cls.DOCTYPE, {'doc_type': dt})
		except:
			...
