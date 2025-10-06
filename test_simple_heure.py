from datetime import time

print("TEST LOGIQUE HEURE LIMITE 7H30")
print("=" * 40)

heure_limite_arrivee = time(7, 30)

heures_test = [
    time(5, 30),   # 5h30
    time(6, 45),   # 6h45
    time(7, 0),    # 7h00
    time(7, 29),   # 7h29
    time(7, 30),   # 7h30
    time(7, 31),   # 7h31
    time(8, 0),    # 8h00
    time(9, 15),   # 9h15
]

for heure_test in heures_test:
    if heure_test < heure_limite_arrivee:
        heure_finale = heure_limite_arrivee
        status = "AJUSTE"
    else:
        heure_finale = heure_test
        status = "NORMAL"
    
    print(f"{heure_test.strftime('%H:%M')} -> {heure_finale.strftime('%H:%M')} [{status}]")

print("\nLogique implementee:")
print("- Pointage avant 7h30 -> Ajuste a 7h30")
print("- Pointage a partir de 7h30 -> Heure reelle")
