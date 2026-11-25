-- Luacheck-asetukset Solar2D-projekteille.

max_line_length = 160

-- Solar2D käyttää Lua 5.1:tä.
std = "lua51"

-- Solar2D:n omat kirjastot, jotka ovat käytettävissä ilman require-kutsua. Niitä ei saa ylikirjoittaa.
read_globals = {
	"audio",
	"display",
	"easing",
	"graphics",
	"media",
	"native",
	"network",
	"Runtime",
	"system",
	"timer",
	"transition",

	-- Roso Games -templatet lisäävät tai korvaavat nämä funktiot Luan ja Solar2D:n omissa kirjastoissa.
	string = {
		fields = {
			count = { read_only = false },
			findLast = { read_only = false },
			formatThousands = { read_only = false },
			split = { read_only = false },
			splitInTwo = { read_only = false },
		},
	},

	table = {
		fields = {
			copy = { read_only = false },
			count = { read_only = false },
			getNext = { read_only = false },
			getRandom = { read_only = false },
			print = { read_only = false },
			shuffle = { read_only = false },
		},
	},

	math = {
		fields = {
			generateSeed = { read_only = false },
			randomseed = { read_only = false },
		},
	},

	display = {
		fields = {
			addRepeatingFill = { read_only = false },
			fitText = { read_only = false },
			getScaleFactor = { read_only = false },
			hex2rgb = { read_only = false },
			isValid = { read_only = false },
			remove = { read_only = false },
			rgb2hex = { read_only = false },
			scaleDisplayObject = { read_only = false },
		},
	},

	system = {
		fields = {
			checkForFile = { read_only = false },
			createFolder = { read_only = false },
			getTruePlatform = { read_only = false },
		},
	},

	transition = {
		fields = {
			ignoreEmptyReference = { read_only = false },
		},
	},

	Runtime = {
		fields = {
			addEventListener = { read_only = false },
			removeEventListener = { read_only = false },
		},
	},
}

-- require( "physics" ) luo myös globaalin physics-muuttujan, joten sen asettaminen on sallittua.
globals = {
	"physics",
}

-- Käyttämätön self-, event- tai alaviivalla alkava parametri on Solar2D-koodissa tavallinen, joten niistä ei varoiteta.
ignore = {
	"212/self",
	"212/event",
	"212/_",
	"212/_*",
}

-- config.lua ja build.settings määrittelevät nämä globaalit muuttujat, joista Solar2D lukee asetukset.
files["**/config.lua"] = {
	globals = { "application" },
}

files["**/build.settings"] = {
	globals = { "settings" },
}

-- Roso Games -templatejen libs/utils.lua luo globaalin utils-taulukon.
files["**/libs/utils.lua"] = {
	globals = { "utils" },
}

-- Valmiit kolmannen osapuolen kirjastot (esim. Ponywolfin ponytiled) asennetaan com-kansioon, eikä niitä tarkisteta.
exclude_files = {
	"**/com/**",

	-- Sama koskee Story Weaver -kirjastoa, joka tulee jokaisen templaten mukana.
	"**/libs/spyricStoryWeaver.lua",
}
