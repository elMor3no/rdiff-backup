# Copyright 2002 2005 Ben Escoto
#
# This file is part of rdiff-backup.
#
# rdiff-backup is free software; you can redistribute it and/or modify
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# rdiff-backup is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with rdiff-backup; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA
"""Invoke rdiff utility to make signatures, deltas, or patch"""

import os
from . import Globals, log, TempFile, rpath, hash, librsync




def find_blocksize(file_len):
    """Return a reasonable block size to use on files of length file_len

	If the block size is too big, deltas will be bigger than is
	necessary.  If the block size is too small, making deltas and
	patching can take a really long time.

	"""
    if file_len < 4096: return 64  # set minimum of 64 bytes
    else:  # Use square root, rounding to nearest 16
        return int(pow(file_len, 0.5) / 16) * 16


def get_delta_sigfileobj(sig_fileobj, rp_new):
    """Like get_delta but signature is in a file object"""
    log.Log(
        "Getting delta of %s with signature stream" % rp_new.get_safepath(), 7)
    return librsync.DeltaFile(sig_fileobj, rp_new.open("rb"))


def get_delta_sigrp(rp_signature, rp_new):
    """Take signature rp and new rp, return delta file object"""
    log.Log(
        "Getting delta of %s with signature %s" %
        (rp_new.get_safepath(), rp_signature.get_safeindexpath()), 7)
    return librsync.DeltaFile(rp_signature.open("rb"), rp_new.open("rb"))


def get_delta_sigrp_hash(rp_signature, rp_new):
    """Like above but also calculate hash of new as close() value"""
    log.Log(
        "Getting delta (with hash) of %s with signature %s" %
        (rp_new.get_safepath(), rp_signature.get_safeindexpath()), 7)
    return librsync.DeltaFile(
        rp_signature.open("rb"), hash.FileWrapper(rp_new.open("rb")))


def write_delta(basis, new, delta, compress=None):
    """Write rdiff delta which brings basis to new"""
    log.Log(
        "Writing delta %s from %s -> %s" %
        (basis.get_safepath(), new.get_safepath(), delta.get_safepath()), 7)
    deltafile = librsync.DeltaFile(get_signature(basis), new.open("rb"))
    delta.write_from_fileobj(deltafile, compress)


def write_patched_fp(basis_fp, delta_fp, out_fp):
    """Write patched file to out_fp given input fps.  Closes input files"""
    rpath.copyfileobj(librsync.PatchedFile(basis_fp, delta_fp), out_fp)
    assert not basis_fp.close() and not delta_fp.close()


def write_via_tempfile(fp, rp):
    """Write fileobj fp to rp by writing to tempfile and renaming"""
    tf = TempFile.new(rp)
    retval = tf.write_from_fileobj(fp)
    rpath.rename(tf, rp)
    return retval


def patch_local(rp_basis, rp_delta, outrp=None, delta_compressed=None):
    """Patch routine that must be run locally, writes to outrp

	This should be run local to rp_basis because it needs to be a real
	file (librsync may need to seek around in it).  If outrp is None,
	patch rp_basis instead.

	The return value is the close value of the delta, so it can be
	used to produce hashes.

	"""

