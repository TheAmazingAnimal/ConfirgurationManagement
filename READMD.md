## Эмулятор командной оболочки ОС (Вариант №7)

### Общее описание

Данный проект представляет собой эмулятор командной оболочки операционной системы, реализованный на языке Python.

Эмулятор работает в виде консольного интерфейса (CLI) и имитирует работу с виртуальной файловой системой (VFS), построенной в оперативной памяти.

---

### Команды

* `ls` - просмотр содержимого текущей директории
* `cd` - переход между директориями виртуальной файловой системы
* `mkdir` - создание директории в VFS
* `pwd` - вывод текущего виртуального пути
* `echo` - вывод текста и значений переменных окружения
* `date` - вывод текущей даты и времени
* `exit` - завершение работы эмулятора

Также реализована обработка основных ошибок команд и раскрытие переменных окружения.

---

### Пример использования

```text
AmazingVFS:/$ ls
repo
AmazingVFS:/$ cd repo
AmazingVFS:/repo/$ pwd
/repo/
AmazingVFS:/repo/$ ls
src
AmazingVFS:/repo/$ cd src
AmazingVFS:/repo/src/$ pwd
/repo/src/
AmazingVFS:/repo/src/$ cd ..
AmazingVFS:/repo/$ mkdir test
AmazingVFS:/repo/$ ls
src test
AmazingVFS:/repo/$ cd test
AmazingVFS:/repo/test/$ pwd
/repo/test/
AmazingVFS:/repo/test/$ echo $HOME
/Users/example
AmazingVFS:/repo/test/$ cd unknown
cd: unknown: No such file or directory
AmazingVFS:/repo/test/$ cd ..
AmazingVFS:/repo/$ exit
Exit CLI
```
