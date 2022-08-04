**Communication entre python et LabView:**

Dans le cadre de notre projet, nous utilisons un des pédales sensix contenant des capteurs. Les données récoltés par les capteurs sont envoyés à une boîte d'acquisition de la marque National-Instrument pour traitement. La carte NI (National-Instrument) est programmée en LabView, les données sont donc disponible sur cette interface de programmation. Pour récupérer les données, il est donc nécessaire de faire communiquer LabView avec python. Il a été choisi d'utiliser le protocol TCP/IP pour cette communication, car celui-ci est très versatile, peut s'interfacer avec de nombreux langages et est simple d'utilisation.



**TCP/IP en python - Le client:**

Le code python se base sur un code préexistant développé pour le logicielle biosiglive, il a été modifié pour s'adapter au mieux à notre problématique.

Par exemple, le transtypage des données vers des "bytes" (octet) se fait avec le module struct.pack (et unpack dans le cas inverse) contraitement au module JSON dans le cas de biosiglive. Celui-ci permet en effet de préciser si les données doivent être écrite en little ou big endian (dans notre cas, on respecte le standard réseau, on utilise donc le big endian).

Autre exemple, dans le cas de biosiglive, on ouvre la connexion et on la ferme à chaque itération. Tandis que dans notre cas, pour des raisons d'optimisation, on ouvre le port une  seule fois au début.

**TCPC/IP Labview - Le server:**



**Structure des données sur Labview:**

On se base sur une matrice de 15 par 10 (15 lignes, 10 colonnes) contenant des floats.

1. Conversion de la matrice en données envoyables sur le TCP/IP

Le client envoie le type de donnée qu'il désire, 

Pour l'exemple on va considérer une attribution arbitraire des données :

- Les forces gauches et droites sont sur la première ligne, chaque force est décomposée en 3 valeurs selon les axes x, y et z (6 valeurs). La nomenclature est FGx pour force gauche sur l'axe x. Ordonnées de droite à gauche avec premièrement les forces relatives au côté gauche puis droit, et en suivant l'ordre x, y et z.

- Les moments sont sur la 3 ème ligne et se décompose de la même manière

- Les torques sont sur la 5ème ligne, il y a le torque gauche et le torque droit.

- les angles sont sur la 7ème ligne, il y a les angles gauche et droit.

- Le reste des données ne sont pour l'instant pas utiliser.

Le serveur reçoit une liste de toutes les coordonnées des données voulues. Et retourne une sur les 4 premiers octets la taille des données qu'il renvoie puis les données ordonnées dans l'ordre de la liste reçue.

Étant donnée que les données échanger sur TCP/IP dans labview doivent être de type string on choisit de faire un transtypage permettant de garder les données sous leur formes binaires, cela nous permet de garder une taille toujours identique d'une donnée quelle que soit la donnée. (exemple: si l'on veut envoyer un float 32, on envoie la valeur binaire du float 32 et non pas une représentation en ASCII). source : https://knowledge.ni.com/KnowledgeArticleDetails?id=kA00Z00000159spSAA&l=en-CA

Il ne faut pas oublier que la matrice est renouvelée à une fréquence d'environ 30Hz. On va donc vérifier que l'on ne doit pas attendre de recevoir qq chose de la part du client pour renouveler la valeur de la matrice.



**Protocole utilisé:**

Le protocole utilisé est bien évidement TCP/IP. On va détailler ici quelles sont les données échangée et leur rôle.

![image-20220804181857459](C:\Users\arsen\AppData\Roaming\Typora\typora-user-images\image-20220804181857459.png) 

Le client commence par envoyé une trame construite comme suit :

1. Les 4 premiers octets représente la taille de la trame (sans compter ces 4 octets) sous forme d'un signed int 32.
2. La deuxième partie de la trame est composée des coordonnées matricielle des données que l'on veut, chaque coordonné est stocké sur un unsigned char pour prendre le moins de place possible, la coordonnées maximum vaut 15 et est donc inférieur à la valeur maximum pouvant être stockée sur un char (255).
3. Le server répond avec un trame dont les 4 premiers octets contiennent la taille des données dans la suite de la trame.
4. La deuxième partie de la trame contient les données dans l'ordre des coordonnées envoyées et sous forme d'unsigned double.

**Queue:**
La queue permet de simuler l'arrivée toutes les 33 ms d'une nouvelle matrice.
Celle-ci permet la communication entre le while générant une nouvelle matrice toutes les 33 ms et le programme principal.
On l'initialise comme ne pouvant contenir qu'un seul élément à la fois. En effet, soit la données est lue soit elle va être réecrite.

**Intégration au programme existant: **

- Pour matcher avec notre programme, il faut donner la matrice à l'entrée de la création de la queue, ce qui permet à la queue d'avoir le bon type de donnée qu'elle va stocker.
- Récuperer le "queue out", contenant le queue refnum et le type des données échangé avec la queue , et le "error in". Cette connexion entre le VI du programme de récolte de données et notre programme se fait dans le VI "Server_LabView.vi" en remplaçant le vi "data array refres.vi" par le VI du programme.
- Une fois les données générées il faut, effacer ce qu'il y a dans la queue (s'il y a qq chose) avec le module dequeue element avec le time out à 0. Puis mettre les données générées dans la queue avec le module Enqueue element (sans time out).

**Performance:**
Pour une matrice de 15 par 10, on peut monter à 100Hz. On envoit donc 150 double (8 octets) en 0.01s donc la transmission est de 150 * 8 * 100 = 120ko/s.