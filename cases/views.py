# cases/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Case, CaseNote
from .forms import CaseForm, CaseNoteForm

@login_required
def case_list(request):
    cases = Case.objects.all()
    return render(request, 'cases/case_list.html', {'cases': cases})

@login_required
def case_detail(request, case_id):
    case = get_object_or_404(Case, id=case_id)
    notes = case.notes.all().order_by('-created_at')
    if request.method == 'POST':
        note_form = CaseNoteForm(request.POST)
        if note_form.is_valid():
            new_note = note_form.save(commit=False)
            new_note.case = case
            new_note.author = request.user
            new_note.save()
            messages.success(request, 'Note added successfully.')
            return redirect('cases:case_detail', case_id=case.id)
    else:
        note_form = CaseNoteForm()
    return render(request, 'cases/case_detail.html', {'case': case, 'notes': notes, 'note_form': note_form})

@login_required
def case_create(request):
    if request.method == 'POST':
        form = CaseForm(request.POST)
        if form.is_valid():
            case = form.save(commit=False)
            case.assigned_lawyer = request.user
            case.save()
            messages.success(request, 'Case created successfully.')
            return redirect('cases:case_detail', case_id=case.id)
    else:
        form = CaseForm()
    return render(request, 'cases/case_form.html', {'form': form})

@login_required
def case_update(request, case_id):
    case = get_object_or_404(Case, id=case_id)
    if request.method == 'POST':
        form = CaseForm(request.POST, instance=case)
        if form.is_valid():
            form.save()
            messages.success(request, 'Case updated successfully.')
            return redirect('cases:case_detail', case_id=case.id)
    else:
        form = CaseForm(instance=case)
    return render(request, 'cases/case_form.html', {'form': form})
