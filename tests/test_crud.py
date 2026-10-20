from registry import crud, schemas


def make_model(db, name="fraud-detector"):
    return crud.create_model(db, schemas.ModelCreate(name=name, description=None))


def make_version(db, model_id, tag, promote=False, framework="PyTorch"):
    return crud.create_version(
        db,
        schemas.VersionCreate(
            model_id=model_id,
            version_tag=tag,
            framework=framework,
            promote_to_current=promote,
        ),
    )


def test_create_model_assigns_an_id(db):
    model = make_model(db)

    assert model.id
    assert crud.get_model(db, model.id) is model


def test_delete_model_removes_it(db):
    model = make_model(db)
    crud.delete_model(db, model.id)

    assert crud.get_model(db, model.id) is None


def test_framework_keeps_the_casing_the_response_schema_requires(db):
    """Regression: crud lowercased framework, so VersionResponse rejected it.

    enum_frameworks validates on its *values* ("PyTorch"), not its lowercase
    member names, so storing "pytorch" made the endpoint return HTTP 500.
    """
    model = make_model(db)
    version = make_version(db, model.id, "1.0.0")

    assert version.framework == "PyTorch"
    assert schemas.VersionResponse.model_validate(version).framework.value == "PyTorch"


def test_version_is_not_current_unless_promoted(db):
    model = make_model(db)
    version = make_version(db, model.id, "1.0.0", promote=False)

    assert not version.current_version
    assert model.current_version_id is None


def test_promoting_a_version_demotes_the_previous_one(db):
    model = make_model(db)
    first = make_version(db, model.id, "1.0.0", promote=True)
    second = make_version(db, model.id, "2.0.0", promote=True)

    db.refresh(first)
    db.refresh(model)

    assert not first.current_version
    assert second.current_version
    assert model.current_version_id == second.id


def test_exactly_one_version_is_current_after_several_promotions(db):
    model = make_model(db)
    for tag in ("1.0.0", "2.0.0", "3.0.0"):
        make_version(db, model.id, tag, promote=True)

    current = [v for v in crud.get_versions(db, model.id) if v.current_version]

    assert len(current) == 1
    assert current[0].version_tag == "3.0.0"


def test_promotion_does_not_affect_another_model(db):
    """The demotion UPDATE must be scoped by model_id."""
    a = make_model(db, "model-a")
    b = make_model(db, "model-b")
    a_current = make_version(db, a.id, "1.0.0", promote=True)
    make_version(db, b.id, "1.0.0", promote=True)

    db.refresh(a_current)

    assert a_current.current_version
