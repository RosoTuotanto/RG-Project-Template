Tähän kansioon tulevat pelin kuvien lähdetiedostot ja testiversiot.

## Sovelluskuvakkeiden luonti

Peli tarvitsee omat kuvaketiedostot Solar2D-simulaattoria ja valmiita julkaisuversioita varten. Voit luoda ne yhdestä lähdekuvasta suoraan GitHubissa, ilman että asennat mitään omalle koneellesi.

1. Tallenna kuvakkeen lähdekuva tähän kansioon nimellä `icon-source.png`.
    - Kuvan tulee olla vähintään **1024 x 1024 pikseliä**. Työkalu ei koskaan suurenna kuvaa, koska se tekisi kuvakkeesta sumean.
    - Kuvan ei tarvitse olla neliö. Jos se ei ole, työkalu rajaa siitä keskeltä suurimman neliön. Rajatunkin neliön tulee olla vähintään 1024 x 1024.
    - Voit käyttää PNG-, JPEG-, WebP- tai BMP-kuvaa. Läpinäkyvyys säilyy.
2. Vie lähdekuva GitHubiin git-työkalullasi (GitHub Desktop, VS Code, komentorivi tai vastaava), samalla tavalla kuin muutkin tiedostot.
3. Avaa repositorio GitHubissa, mene **Actions**-välilehdelle, valitse vasemmalta **Generate app icons** ja paina **Run workflow**.
    - Kenttään on valmiiksi täytetty polku `developmentFiles/images/icon-source.png`. Jos annoit kuvalle toisen nimen tai tallensit sen muualle, kirjoita kuvan polku tähän.
    - Paina lopuksi vihreää **Run workflow** -painiketta.
4. Odota, että ajo valmistuu. Avaa valmis ajo ja lataa sivun alalaidasta **Artifacts**-kohdasta paketti **app-icons** (lataaminen edellyttää, että olet kirjautunut GitHubiin). Zip-tiedoston sisällä on kolme tiedostoa: `Icon.png`, `Icon-win32.ico` ja `Icon-osx.icns`.
5. Pura zipin kolme tiedostoa **`game/`**-kansioon eli peliprojektin juureen (samaan paikkaan kuin `main.lua` ja `config.lua`).
6. Committaa ja pushaa nämä kolme tiedostoa git-työkalullasi. Työkalu ei tee sitä puolestasi.

Jos ajo epäonnistuu, avaa ajon **Summary**-sivu. Se kertoo selkokielellä, mikä meni pieleen: yleensä kuvaa ei löytynyt annetusta polusta, tiedosto ei ollut kuva, tai kuva oli liian pieni (alle 1024 x 1024). Korjaa ongelma ja aja työnkulku uudelleen.
