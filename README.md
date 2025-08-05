# Ro-Crate SIS Specifications Directory


## Purpose

This repository contains Profiles/Modules specifications to use with RO-Crate.

It serves as a permanent URL for these specifications.

## Structure

Each specification is in a separate directory.

```
/specification-name/
```

This directory contains different versions, each identified by a directory names.

```
/specification-name/A.B.x/
```

Each version contains a specification file, `spec.md`. 

The specification file indicates which RO-Crate versions it is compatible with. 

PATCH versions are contained in the same directory, PATCHES are intended to fix issues that do not change the workings of the specification, e.g. typos. 

Aside from this, the specifications are not changed after release.

```
/specification-name/A.B.x/spec.md
```

It may also contain library code in both source and compiled forms, if applicable.

```
/specification-name/A.B.x/spec.md/lib/
```