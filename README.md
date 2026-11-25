# Roso Games

Tervetuloa ryhmäsi GitHub-repositorioon! Tänne kootaan kaikki ryhmäsi yhteisen pelin tiedostot: koodi, grafiikat, äänet ja muut materiaalit.

Kun ryhmä on valinnut toteutettavan peli-idean ja sen pohjaksi tulevan Roso Games Templaten, template lisätään `game`-kansioon. Templaten dokumentaatio ja tarinatiedosto tulevat `developmentFiles`-kansioon.

## Repositorion rakenne

- **game**: pelin pääkansio. Tänne tulee valittu Roso Games Template ja kaikki, mitä peli tarvitsee toimiakseen.
- **developmentFiles**: kehityksessä käytettävät lähdetiedostot sekä raaka- ja testiversiot, joita ei sisällytetä itse peliin (esim. tasoja sisältävät kuvatiedostot ja ääniprojektit).
  - **pitch**: äänestyksen voittaneen peli-idean pitch-materiaalit. Ne lisätään tänne äänestyksen jälkeen. Muita pitchejä ei lisätä repositorioon.
- **.github**: GitHub-automaatiot. Osallistujien ei tarvitse koskea näihin tiedostoihin. Automaatiot voivat jättää committeihin kommentteja (esim. luacheck-raportti ja tyyliehdotukset). Kommentit ovat pelkkiä ehdotuksia: ne eivät muuta mitään, ja ne saa vapaasti ohittaa.

## Työskentely

- Lisää ja päivitä tiedostot Gitin avulla, esimerkiksi GitHub Desktop -sovelluksella, äläkä GitHubin verkkosivun kautta. Sovelluksella voit myös muokata ja poistaa tiedostoja, ja koko projekti on aina myös omalla koneellasi.
- Kirjaa tehtävät, bugit ja kysymykset issueiksi valmiiden lomakkeiden avulla.
- Repositorion AGENTS.md- ja CLAUDE.md-tiedostot ohjeistavat Claude Coden kaltaisia tekoälyavustajia toimimaan tässä projektissa tuutorina: ne selittävät asioita, antavat vinkkejä ja voivat käydä kirjoittamasi koodin läpi ja kertoa, missä on vikaa, mutta eivät tee peliä puolestasi. Syyt tähän löydät oppitunnilta [Tekoälyn hyödyntäminen](https://www.rosogames.fi/lms/1-tyokalut-ja-orientaatio/lessons/tekoalyn-hyodyntaminen/).
- Tiedostojen poistamista ei suositella. Jos ne halutaan silti poistaa, siitä päättää koko ryhmä yhdessä eikä kukaan yksin, koska päätös koskee koko ryhmän peliä.

---

**Huomio:** Ryhmäsi pelin materiaalit on tarkoitettu vain ryhmäsi sisäiseen käyttöön. Älä jaa niitä eteenpäin julkisesti.

**Osallistujalisenssi:** Roso Gamesin osallistujalisenssi on tämän repositorion [OSALLISTUJALISENSSI.md](OSALLISTUJALISENSSI.md)-tiedostossa ja Roso Gamesin verkkosivuilla osoitteessa [www.rosogames.fi/osallistujalisenssi](https://www.rosogames.fi/osallistujalisenssi/).

## Muut Roso Games -materiaalit

- [RG-Game-Templates](https://github.com/RosoTuotanto/RG-Game-Templates): Roso Games Templatejen lähdekoodit. Jokaisen ryhmän peli tehdään jonkin näistä templateista pohjalle.
- [RG-Learning-Materials](https://github.com/RosoTuotanto/RG-Learning-Materials): kurssien kotitehtävät vastauksineen ja opetuspelien lähdekoodit kehitysvaiheittain. Opetuspelit ja demot, kuten demo [Mitä Roso Games Templateista voisi tehdä?](https://rosotuotanto.github.io/RG-Learning-Materials/demos/template-showcase/), ovat pelattavissa selaimessa [oppimateriaalien verkkosivustolla](https://rosotuotanto.github.io/RG-Learning-Materials/).
- [Oppimisympäristö](https://www.rosogames.fi/opetus): Roso Gamesin kurssit ja oppitunnit.

## Tekijä

[© 2025-2026 Eetu Rantanen](https://www.erantanen.com)

Repositoriossa valmiina olleet tiedostot (RG-Project-Template) on tehty Roso-tuotannon Roso Games -projekteja varten.

## Lisenssi

[MIT](LICENSE)

MIT-lisenssi koskee tiedostoja, jotka olivat repositoriossa valmiina ennen ryhmän työtä (RG-Project-Template), kuten tätä README:tä ja GitHub-automaatioita. Niiden tekijänoikeudet kuuluvat Eetu Rantaselle ja Roso Gamesille (Kukunori ry). Myös `game`-kansioon tulevan Roso Games Templaten oma koodi on MIT-lisensoitu. Templaten kirjastojen, fontin, grafiikan ja äänien lisenssit on lueteltu RG-Game-Templates-repositorion [NOTICE.md](https://github.com/RosoTuotanto/RG-Game-Templates/blob/main/NOTICE.md)-tiedostossa. Ryhmän itse tekemä peli ja sen koodi eivät ole MIT-lisensoituja eivätkä avointa lähdekoodia: ne kuuluvat ryhmälle ja ovat vain ryhmän omassa käytössä. Niihin sovelletaan osallistujalisenssiä.
