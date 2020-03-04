import importlib

class I18N:
	
	def __init__(self, file="i18n_locale"):
		self.file = file
		self.locale = []
		self.reload_locale()
	
	def reload_locale(self):
		file_locale = importlib.import_module("i18n_locale").locale
		print("Imported locale: ", file_locale)
		self.locale = file_locale

	def __getitem__(self, key):
		if key not in self.locale:
			print(f"{key} not found in localization")
			return key
		else:
			return self.locale[key]
	

default = I18N()
