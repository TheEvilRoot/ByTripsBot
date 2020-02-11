
class I18N:
	
	def __init__(self):
		self.locale = []
		self.reload_locale()
	
	def reload_locale(self):
		from i18n_locale import locale as file_locale
		self.locale = file_locale
	
	def __getitem__(self, key):
		values = [v for (k, v) in self.locale if k == key]
		if len(values) == 0:
			return key
		else:
			return values[0]
	

default = I18N()
