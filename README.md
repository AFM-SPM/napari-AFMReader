# napari-AFMReader

A [Napari](https://napari.org/) plugin to read in Atomic Force Microscopy (AFM) files via our sister software [AFMReader](https://github.com/AFM-SPM/AFMReader.git).

You can drag and drop your favourite AFM image files directly into the Napari viewer to use the awesome tools the image analysis community have developed over at the [Napari Hub](https://www.napari-hub.org/) to analyse your images using open-source software and a GUI!

| File Extension | Supported by AFMReader | Description |
| --- | --- | --- |
| asd | ✅ | High-speed AFM format. |
| gwy | ✅ | Gwyddion saved format. |
| ibw | ✅ | Igor binary-wave format. |
| jpk | ✅ | JPK instruments format. |
| spm | ✅ | Bruker spm format. |
| stp | ✅ | Homemade stp format. |
| top | ✅ | Homemade top format. |
| topostats | ✅ | TopoStats output format. |

## Installation

### Via Napari-Hub

This software should be installable directly from Napari!

All you need to do is:
1. Open Napari by typing the `napari` into your command line with your [Napari environment activated](https://napari.org/stable/tutorials/fundamentals/installation.html).

    ```
    napari
    ```

2. Go to `Plugins` > `Install/Uninstall Plugins`, and search for `napari-afmreader`.


### Via Git

Occasionally the Napari-Hub version of `napari-AFMReader` may not be the most up-to-date. This is when you might want to install both `AFMReader` and `napari-AFMReader` via Git.

`napari-AFMReader` has been designed to need minimal maintenance, with most of the new file type additions being solely added to AFMReader.

1. With [Git installed](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) on your machine, clone both the `AFMReader` and `napari-AFMReader` repositories:
    
    ```
    git clone https://github.com/AFM-SPM/AFMReader.git
    ```
    ```
    git clone https://github.com/AFM-SPM/napari-AFMReader.git
    ```

2. Activate your Python environment (e.g. Conda) and install the dependencies for each - make sure that the `AFMReader` dependency is installed second!
    ```
    cd napari-AFMReader
    pip install .
    cd ..
    ```
    ```
    cd AFMReader
    pip install .
    ```

3. Now when you open Napari via the `napari` command, it should use the latest version of `AFMReader`, and `napari-AFMReader`.

    ```
    napari
    ```


## Usage

This package should be fairly straight-forward and intuitive to use, requiring you to:

1. Drag and drop your supported AFM file format into the Napari Viewer.

2. Type in the name of the channel you'd like to use*.

    **Possible channel names will not appear at first due to the order in which AFMReader processes an image. Thus, when provided with an non-existent channel name, the dialogue box will then return a list of possible channels to choose from.*


